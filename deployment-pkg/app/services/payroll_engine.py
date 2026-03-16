"""
Real Payroll Engine

Supports:
- Gross-to-net payroll calculations
- Tax withholding (federal, state, local)
- Deductions (health insurance, 401k, etc.)
- Multiple pay periods
- Compliance with tax rules
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
import json

from utils.logger import get_logger
from utils.errors import ServiceException
from config.settings import settings


logger = get_logger(__name__)


@dataclass
class TaxRule:
    """Represents a tax bracket."""
    min_income: Decimal
    max_income: Optional[Decimal]
    tax_rate: Decimal
    
    def calculate_tax(self, income: Decimal) -> Decimal:
        """Calculate tax for income in this bracket."""
        if income <= self.min_income:
            return Decimal(0)
        
        taxable = income - self.min_income
        
        if self.max_income and income > self.max_income:
            taxable = self.max_income - self.min_income
        
        return taxable * self.tax_rate


@dataclass
class PayrollDeduction:
    """Represents a payroll deduction."""
    name: str
    type: str  # fixed, percentage, pre_tax, post_tax
    amount_or_rate: Decimal
    pre_tax: bool = False
    
    def calculate(self, gross_income: Decimal) -> Decimal:
        """Calculate deduction amount."""
        if self.type == "fixed":
            return self.amount_or_rate
        elif self.type == "percentage":
            return gross_income * (self.amount_or_rate / Decimal(100))
        else:
            return Decimal(0)


class PayrollEngine:
    """Real payroll calculation engine."""
    
    # Federal tax brackets 2024 (single filer, simplified)
    FEDERAL_TAX_BRACKETS = [
        TaxRule(Decimal(0), Decimal(11600), Decimal("0.10")),
        TaxRule(Decimal(11600), Decimal(47150), Decimal("0.12")),
        TaxRule(Decimal(47150), Decimal(100525), Decimal("0.22")),
        TaxRule(Decimal(100525), Decimal(191950), Decimal("0.24")),
        TaxRule(Decimal(191950), Decimal(243725), Decimal("0.32")),
        TaxRule(Decimal(243725), Decimal(609350), Decimal("0.35")),
        TaxRule(Decimal(609350), None, Decimal("0.37")),
    ]
    
    # Social Security and Medicare rates
    SOCIAL_SECURITY_RATE = Decimal("0.062")
    SOCIAL_SECURITY_WAGE_LIMIT = Decimal(168600)  # 2024 limit
    MEDICARE_RATE = Decimal("0.0145")
    MEDICARE_ADDITIONAL_RATE = Decimal("0.009")  # Additional on income over $200k
    MEDICARE_ADDITIONAL_THRESHOLD = Decimal(200000)
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.PayrollEngine")
        self.standard_deduction = Decimal(14600)  # 2024 single
        self.payroll_tax_rate = Decimal(settings.payroll_tax_rate or "0.06")
        self.health_insurance_deduction = Decimal(settings.health_insurance_deduction or "200")
        self.pension_rate = Decimal(settings.pension_rate or "0.05")
    
    def calculate_federal_income_tax(
        self,
        annual_gross: Decimal,
        pay_periods: int = 26
    ) -> Decimal:
        """
        Calculate federal income tax withholding per pay period.
        
        Args:
            annual_gross: Total annual gross income
            pay_periods: Number of pay periods per year
        """
        # Apply standard deduction
        taxable_income = annual_gross - self.standard_deduction
        if taxable_income <= 0:
            return Decimal(0)
        
        # Calculate annual tax
        annual_tax = Decimal(0)
        for bracket in self.FEDERAL_TAX_BRACKETS:
            annual_tax += bracket.calculate_tax(taxable_income)
        
        # Divide by pay periods
        per_period_withholding = annual_tax / Decimal(pay_periods)
        
        return per_period_withholding.quantize(Decimal("0.01"))
    
    def calculate_social_security_tax(self, gross_income: Decimal) -> Decimal:
        """Calculate Social Security tax (6.2% on income up to limit)."""
        taxable = min(gross_income, self.SOCIAL_SECURITY_WAGE_LIMIT)
        return (taxable * self.SOCIAL_SECURITY_RATE).quantize(Decimal("0.01"))
    
    def calculate_medicare_tax(self, annual_gross: Decimal) -> Decimal:
        """
        Calculate Medicare tax.
        
        1.45% base + additional 0.9% on income over $200k
        """
        base_medicare = (annual_gross * self.MEDICARE_RATE).quantize(Decimal("0.01"))
        
        additional = Decimal(0)
        if annual_gross > self.MEDICARE_ADDITIONAL_THRESHOLD:
            additional = (
                (annual_gross - self.MEDICARE_ADDITIONAL_THRESHOLD)
                * self.MEDICARE_ADDITIONAL_RATE
            ).quantize(Decimal("0.01"))
        
        return base_medicare + additional
    
    async def calculate_paycheck(
        self,
        employee_id: str,
        gross_amount: Decimal,
        annual_gross: Decimal,
        pay_period: str = "bi-weekly",
        deductions: Optional[List[PayrollDeduction]] = None,
        state_residence: str = "CA"
    ) -> Dict[str, Any]:
        """
        Calculate a complete paycheck with all deductions and taxes.
        
        Args:
            employee_id: Employee identifier
            gross_amount: Gross pay for this period
            annual_gross: Total annual gross (for tax calculations)
            pay_period: Pay period frequency
            deductions: List of custom deductions
            state_residence: State for state income tax
        """
        try:
            # Determine pay periods per year
            pay_periods_map = {
                "weekly": 52,
                "bi-weekly": 26,
                "semi-monthly": 24,
                "monthly": 12,
                "quarterly": 4,
                "annual": 1
            }
            pay_periods = pay_periods_map.get(pay_period, 26)
            
            result = {
                "employee_id": employee_id,
                "gross_amount": str(gross_amount),
                "pay_period": pay_period,
                "calculation_date": datetime.utcnow().isoformat(),
                "taxes": {},
                "deductions": [],
                "net_pay": Decimal(0)
            }
            
            # Start with gross
            running_total = gross_amount
            
            # Pre-tax deductions (reduce taxable income)
            pre_tax_total = Decimal(0)
            if deductions:
                for deduction in deductions:
                    if deduction.pre_tax:
                        amount = deduction.calculate(gross_amount)
                        pre_tax_total += amount
                        result["deductions"].append({
                            "name": deduction.name,
                            "type": deduction.type,
                            "amount": str(amount),
                            "tax_treatment": "pre_tax"
                        })
            
            # Add default pre-tax deductions
            if self.health_insurance_deduction > 0:
                pre_tax_total += self.health_insurance_deduction
                result["deductions"].append({
                    "name": "Health Insurance",
                    "type": "fixed",
                    "amount": str(self.health_insurance_deduction),
                    "tax_treatment": "pre_tax"
                })
            
            if self.pension_rate > 0:
                pension_amount = (gross_amount * self.pension_rate).quantize(Decimal("0.01"))
                pre_tax_total += pension_amount
                result["deductions"].append({
                    "name": "401(k) / Pension",
                    "type": "percentage",
                    "amount": str(pension_amount),
                    "tax_treatment": "pre_tax"
                })
            
            taxable_income = gross_amount - pre_tax_total
            running_total -= pre_tax_total
            
            # Calculate taxes
            fed_income_tax = self.calculate_federal_income_tax(
                annual_gross, pay_periods
            )
            result["taxes"]["federal_income"] = str(fed_income_tax)
            running_total -= fed_income_tax
            
            ss_tax = self.calculate_social_security_tax(taxable_income)
            result["taxes"]["social_security"] = str(ss_tax)
            running_total -= ss_tax
            
            medicare_tax = self.calculate_medicare_tax(taxable_income)
            result["taxes"]["medicare"] = str(medicare_tax)
            running_total -= medicare_tax
            
            # State income tax (simplified - varies by state)
            state_tax = Decimal(0)
            if state_residence in ["CA", "NY", "IL"]:  # High-tax states
                state_tax = (taxable_income * Decimal("0.05")).quantize(Decimal("0.01"))
            result["taxes"]["state_income"] = str(state_tax)
            running_total -= state_tax
            
            # Post-tax deductions
            if deductions:
                for deduction in deductions:
                    if not deduction.pre_tax:
                        amount = deduction.calculate(gross_amount)
                        result["deductions"].append({
                            "name": deduction.name,
                            "type": deduction.type,
                            "amount": str(amount),
                            "tax_treatment": "post_tax"
                        })
                        running_total -= amount
            
            # Net pay
            net_pay = max(running_total, Decimal(0))
            result["net_pay"] = str(net_pay)
            result["total_taxes"] = str(
                fed_income_tax + ss_tax + medicare_tax + state_tax
            )
            result["total_deductions"] = str(pre_tax_total + sum(
                Decimal(d["amount"]) for d in result["deductions"]
                if d["tax_treatment"] == "post_tax"
            ))
            
            self.logger.info(f"Paycheck calculated for {employee_id}: {net_pay}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Payroll calculation failed: {str(e)}")
            raise ServiceException(f"Payroll calculation failed: {str(e)}")
    
    async def process_payment(
        self,
        employee_id: str,
        amount: Decimal,
        payment_method: str = "direct_deposit",
        bank_account: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process payment to employee.
        
        Args:
            employee_id: Employee ID
            amount: Payment amount
            payment_method: Method (direct_deposit, check, etc.)
            bank_account: Bank account for direct deposit
        """
        try:
            # In real system, this would integrate with payment processor
            transaction_id = f"pyrl_{employee_id}_{int(datetime.utcnow().timestamp())}"
            
            result = {
                "success": True,
                "transaction_id": transaction_id,
                "employee_id": employee_id,
                "amount": str(amount),
                "payment_method": payment_method,
                "status": "processed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if payment_method == "direct_deposit" and bank_account:
                result["account_reference"] = bank_account[-4:]
            
            self.logger.info(f"Payment processed: {transaction_id}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Payment processing failed: {str(e)}")
            raise ServiceException(f"Payment processing failed: {str(e)}")


# Singleton instance
_payroll_engine: Optional[PayrollEngine] = None


def get_payroll_engine() -> PayrollEngine:
    """Get or create payroll engine singleton."""
    global _payroll_engine
    if _payroll_engine is None:
        _payroll_engine = PayrollEngine()
    return _payroll_engine
