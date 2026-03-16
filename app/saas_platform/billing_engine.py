"""
Billing and usage metering engine for multi-tenant SaaS platform.

Handles usage tracking, billing calculations, quota enforcement, and invoicing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

from saas_platform.models import (
    UsageMetric, BillingEvent, Subscription, Invoice, SubscriptionPlan,
    SubscriptionPlanDefinition, UsageMetricType, MetricBillingType, BillingModel,
    generate_platform_id
)


logger = logging.getLogger(__name__)


class BillingCalculator:
    """Calculates billing amounts."""
    
    def __init__(self):
        """Initialize billing calculator."""
        self.plan_definitions = self._init_plan_definitions()
    
    def _init_plan_definitions(self) -> Dict[SubscriptionPlan, SubscriptionPlanDefinition]:
        """Initialize subscription plan definitions."""
        return {
            SubscriptionPlan.FREE: SubscriptionPlanDefinition(
                plan_id=generate_platform_id("plan"),
                plan_name=SubscriptionPlan.FREE,
                monthly_price=0.0,
                annual_price=0.0,
                billing_model=BillingModel.FLAT_RATE,
                features={
                    "apps": {"included": True, "limit": 3},
                    "workflows": {"included": True, "limit": 10},
                    "api_calls": {"included": True, "limit": 10000},
                    "storage": {"included": True, "limit": 5},
                    "users": {"included": True, "limit": 1},
                    "advanced_analytics": {"included": False}
                }
            ),
            SubscriptionPlan.STARTER: SubscriptionPlanDefinition(
                plan_id=generate_platform_id("plan"),
                plan_name=SubscriptionPlan.STARTER,
                monthly_price=29.0,
                annual_price=290.0,
                billing_model=BillingModel.HYBRID,
                features={
                    "apps": {"included": True, "limit": 20},
                    "workflows": {"included": True, "limit": 50},
                    "api_calls": {"included": True, "limit": 100000},
                    "storage": {"included": True, "limit": 50},
                    "users": {"included": True, "limit": 5},
                    "custom_domains": {"included": False, "limit": 1},
                    "advanced_analytics": {"included": False}
                },
                overage_pricing={
                    "api_calls": 0.0001,
                    "storage": 0.1
                }
            ),
            SubscriptionPlan.PROFESSIONAL: SubscriptionPlanDefinition(
                plan_id=generate_platform_id("plan"),
                plan_name=SubscriptionPlan.PROFESSIONAL,
                monthly_price=99.0,
                annual_price=990.0,
                billing_model=BillingModel.HYBRID,
                features={
                    "apps": {"included": True, "limit": 100},
                    "workflows": {"included": True, "limit": 200},
                    "api_calls": {"included": True, "limit": 1000000},
                    "storage": {"included": True, "limit": 500},
                    "users": {"included": True, "limit": 25},
                    "custom_domains": {"included": True, "limit": 5},
                    "advanced_analytics": {"included": True}
                },
                overage_pricing={
                    "api_calls": 0.00005,
                    "storage": 0.05
                }
            ),
            SubscriptionPlan.ENTERPRISE: SubscriptionPlanDefinition(
                plan_id=generate_platform_id("plan"),
                plan_name=SubscriptionPlan.ENTERPRISE,
                monthly_price=499.0,
                annual_price=4990.0,
                billing_model=BillingModel.FLAT_RATE,
                features={
                    "apps": {"included": True},
                    "workflows": {"included": True},
                    "api_calls": {"included": True},
                    "storage": {"included": True},
                    "users": {"included": True},
                    "custom_domains": {"included": True},
                    "advanced_analytics": {"included": True},
                    "sso": {"included": True},
                    "dedicated_support": {"included": True}
                }
            )
        }
    
    def get_plan_definition(self, plan: SubscriptionPlan) -> SubscriptionPlanDefinition:
        """Get plan definition."""
        return self.plan_definitions.get(plan)
    
    def calculate_monthly_charge(self, plan: SubscriptionPlan, annual: bool = False) -> float:
        """Calculate monthly charge for plan."""
        definition = self.get_plan_definition(plan)
        if annual:
            return definition.annual_price
        return definition.monthly_price
    
    def calculate_overage_charges(
        self,
        usage: Dict[str, float],
        plan: SubscriptionPlan,
        quotas: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate overage charges."""
        definition = self.get_plan_definition(plan)
        overages = {}
        
        for metric, used in usage.items():
            limit = quotas.get(metric, 0)
            
            if used > limit and metric in definition.overage_pricing:
                overage_units = used - limit
                price_per_unit = definition.overage_pricing[metric]
                overages[metric] = overage_units * price_per_unit
        
        return overages
    
    def calculate_invoice_amount(
        self,
        subscription: Subscription,
        overage_amounts: Dict[str, float],
        tax_rate: float = 0.0
    ) -> Tuple[float, float, float]:
        """Calculate invoice total. Returns (base, overage, tax, total)."""
        plan_definition = self.get_plan_definition(subscription.plan)
        
        base_amount = plan_definition.monthly_price
        overage_amount = sum(overage_amounts.values())
        subtotal = base_amount + overage_amount
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        return base_amount, overage_amount, tax_amount


class UsageTracker:
    """Tracks usage metrics."""
    
    def __init__(self):
        """Initialize usage tracker."""
        self.metrics: Dict[str, UsageMetric] = {}
        self.tenant_metrics: Dict[str, List[str]] = {}
    
    def record_metric(
        self,
        tenant_id: str,
        metric_type: UsageMetricType,
        unit: str,
        value: float,
        billing_type: MetricBillingType = MetricBillingType.INCLUDED
    ) -> UsageMetric:
        """Record usage metric."""
        metric_id = generate_platform_id("metric")
        
        metric = UsageMetric(
            metric_id=metric_id,
            tenant_id=tenant_id,
            metric_type=metric_type,
            billing_type=billing_type,
            unit=unit,
            value=value,
            period="monthly"
        )
        
        self.metrics[metric_id] = metric
        
        if tenant_id not in self.tenant_metrics:
            self.tenant_metrics[tenant_id] = []
        self.tenant_metrics[tenant_id].append(metric_id)
        
        return metric
    
    def get_tenant_usage_this_month(
        self,
        tenant_id: str
    ) -> Dict[str, float]:
        """Get tenant usage for current month."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage_summary = {}
        metric_ids = self.tenant_metrics.get(tenant_id, [])
        
        for mid in metric_ids:
            metric = self.metrics.get(mid)
            if not metric or metric.timestamp < month_start:
                continue
            
            metric_key = f"{metric.metric_type.value}"
            if metric_key not in usage_summary:
                usage_summary[metric_key] = 0.0
            usage_summary[metric_key] += metric.value
        
        return usage_summary
    
    def get_tenant_metrics(self, tenant_id: str, days: int = 30) -> List[UsageMetric]:
        """Get tenant metrics for period."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        metric_ids = self.tenant_metrics.get(tenant_id, [])
        
        metrics = []
        for mid in metric_ids:
            metric = self.metrics.get(mid)
            if metric and metric.timestamp > cutoff:
                metrics.append(metric)
        
        return sorted(metrics, key=lambda m: m.timestamp, reverse=True)


class BillingEventLogger:
    """Logs billing events for audit and analytics."""
    
    def __init__(self):
        """Initialize event logger."""
        self.events: Dict[str, BillingEvent] = {}
        self.tenant_events: Dict[str, List[str]] = {}
    
    def log_event(
        self,
        tenant_id: str,
        event_type: str,
        quantity: float,
        unit_cost: float = 0.0
    ) -> BillingEvent:
        """Log billing event."""
        event_id = generate_platform_id("event")
        
        event = BillingEvent(
            event_id=event_id,
            tenant_id=tenant_id,
            event_type=event_type,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost
        )
        
        self.events[event_id] = event
        
        if tenant_id not in self.tenant_events:
            self.tenant_events[tenant_id] = []
        self.tenant_events[tenant_id].append(event_id)
        
        logger.info(f"Logged billing event: {event_type} for tenant {tenant_id}")
        return event
    
    def get_tenant_events(
        self,
        tenant_id: str,
        event_type: Optional[str] = None,
        days: int = 30
    ) -> List[BillingEvent]:
        """Get billing events for tenant."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        event_ids = self.tenant_events.get(tenant_id, [])
        
        events = []
        for eid in event_ids:
            event = self.events.get(eid)
            if not event or event.timestamp < cutoff:
                continue
            if event_type and event.event_type != event_type:
                continue
            events.append(event)
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)
    
    def calculate_event_revenue(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate revenue from events in period."""
        event_ids = self.tenant_events.get(tenant_id, [])
        total = 0.0
        
        for eid in event_ids:
            event = self.events.get(eid)
            if not event or event.timestamp < start_date or event.timestamp > end_date:
                continue
            total += event.total_cost
        
        return total


class QuotaEnforcer:
    """Enforces tenant quotas."""
    
    def __init__(self, usage_tracker: UsageTracker):
        """Initialize quota enforcer."""
        self.usage_tracker = usage_tracker
    
    def check_quota(
        self,
        tenant_id: str,
        metric: str,
        current_value: float,
        quota_limit: float
    ) -> Tuple[bool, float]:
        """Check if quota is exceeded. Returns (is_allowed, percentage_used)."""
        if quota_limit <= 0:
            return True, 0.0
        
        percentage = (current_value / quota_limit) * 100
        
        if current_value > quota_limit:
            logger.warning(
                f"Quota exceeded for tenant {tenant_id}: "
                f"{metric} = {current_value}/{quota_limit} ({percentage:.1f}%)"
            )
            return False, percentage
        
        return True, percentage
    
    def get_quota_status(
        self,
        tenant_id: str,
        current_usage: Dict[str, float],
        quotas: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """Get quota status for all metrics."""
        status = {}
        
        for metric, limit in quotas.items():
            used = current_usage.get(metric, 0.0)
            is_allowed, percentage = self.check_quota(tenant_id, metric, used, limit)
            
            status[metric] = {
                "used": used,
                "limit": limit,
                "percentage_used": percentage,
                "allowed": is_allowed,
                "remaining": max(0, limit - used)
            }
        
        return status


class InvoiceGenerator:
    """Generates invoices for subscriptions."""
    
    def __init__(
        self,
        billing_calculator: BillingCalculator,
        event_logger: BillingEventLogger
    ):
        """Initialize invoice generator."""
        self.billing_calculator = billing_calculator
        self.event_logger = event_logger
        self.invoices: Dict[str, Invoice] = {}
        self.tenant_invoices: Dict[str, List[str]] = {}
    
    def generate_invoice(
        self,
        subscription: Subscription,
        overages: Dict[str, float],
        tax_rate: float = 0.0
    ) -> Invoice:
        """Generate invoice for subscription."""
        invoice_id = generate_platform_id("invoice")
        
        base, overage, tax = self.billing_calculator.calculate_invoice_amount(
            subscription,
            overages,
            tax_rate
        )
        
        total = base + overage + tax
        
        # Create line items
        line_items = [
            {
                "description": f"{subscription.plan.value} Plan",
                "amount": base
            }
        ]
        
        for metric, amount in overages.items():
            line_items.append({
                "description": f"{metric} Overage",
                "amount": amount
            })
        
        invoice = Invoice(
            invoice_id=invoice_id,
            tenant_id=subscription.tenant_id,
            subscription_id=subscription.subscription_id,
            period_start=subscription.billing_cycle_start,
            period_end=subscription.billing_cycle_end,
            base_amount=base,
            overage_amount=overage,
            tax_amount=tax,
            total_amount=total,
            line_items=line_items,
            issued_at=datetime.utcnow()
        )
        
        self.invoices[invoice_id] = invoice
        
        if subscription.tenant_id not in self.tenant_invoices:
            self.tenant_invoices[subscription.tenant_id] = []
        self.tenant_invoices[subscription.tenant_id].append(invoice_id)
        
        logger.info(f"Generated invoice: {invoice_id} for tenant {subscription.tenant_id}")
        return invoice
    
    def mark_invoice_paid(self, invoice_id: str) -> bool:
        """Mark invoice as paid."""
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            logger.error(f"Invoice not found: {invoice_id}")
            return False
        
        invoice.status = "paid"
        invoice.paid_at = datetime.utcnow()
        
        logger.info(f"Marked invoice as paid: {invoice_id}")
        return True
    
    def get_tenant_invoices(self, tenant_id: str) -> List[Invoice]:
        """Get invoices for tenant."""
        invoice_ids = self.tenant_invoices.get(tenant_id, [])
        return [self.invoices[iid] for iid in invoice_ids if iid in self.invoices]
    
    def get_overdue_invoices(self) -> List[Invoice]:
        """Get overdue invoices."""
        now = datetime.utcnow()
        overdue = []
        
        for invoice in self.invoices.values():
            if (invoice.status == "issued" and
                invoice.due_at and
                invoice.due_at < now):
                overdue.append(invoice)
        
        return overdue


class BillingEngine:
    """Main billing engine orchestrating all operations."""
    
    def __init__(self):
        """Initialize billing engine."""
        self.calculator = BillingCalculator()
        self.usage_tracker = UsageTracker()
        self.event_logger = BillingEventLogger()
        self.quota_enforcer = QuotaEnforcer(self.usage_tracker)
        self.invoice_generator = InvoiceGenerator(
            self.calculator,
            self.event_logger
        )
        self.subscriptions: Dict[str, Subscription] = {}
        self.tenant_subscription: Dict[str, str] = {}
    
    def create_subscription(
        self,
        tenant_id: str,
        plan: SubscriptionPlan,
        auto_renew: bool = True
    ) -> Subscription:
        """Create subscription for tenant."""
        subscription_id = generate_platform_id("sub")
        
        now = datetime.utcnow()
        cycle_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate cycle end (end of current month)
        if now.month == 12:
            cycle_end = cycle_start.replace(year=now.year + 1, month=1) - timedelta(days=1)
        else:
            cycle_end = cycle_start.replace(month=now.month + 1) - timedelta(days=1)
        
        cycle_end = cycle_end.replace(hour=23, minute=59, second=59)
        
        subscription = Subscription(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            plan=plan,
            billing_cycle_start=cycle_start,
            billing_cycle_end=cycle_end,
            auto_renew=auto_renew
        )
        
        self.subscriptions[subscription_id] = subscription
        self.tenant_subscription[tenant_id] = subscription_id
        
        logger.info(f"Created subscription: {subscription_id} for tenant {tenant_id} - Plan: {plan}")
        return subscription
    
    def get_tenant_subscription(self, tenant_id: str) -> Optional[Subscription]:
        """Get subscription for tenant."""
        sub_id = self.tenant_subscription.get(tenant_id)
        return self.subscriptions.get(sub_id) if sub_id else None
    
    def upgrade_subscription(
        self,
        tenant_id: str,
        new_plan: SubscriptionPlan
    ) -> Optional[Subscription]:
        """Upgrade tenant subscription."""
        subscription = self.get_tenant_subscription(tenant_id)
        if not subscription:
            logger.error(f"Subscription not found for tenant: {tenant_id}")
            return None
        
        old_plan = subscription.plan
        subscription.plan = new_plan
        
        logger.info(f"Upgraded subscription for tenant {tenant_id} from {old_plan} to {new_plan}")
        return subscription
    
    def record_usage(
        self,
        tenant_id: str,
        metric_type: UsageMetricType,
        value: float
    ) -> Optional[UsageMetric]:
        """Record usage for billing."""
        return self.usage_tracker.record_metric(
            tenant_id,
            metric_type,
            metric_type.value,
            value
        )
    
    def process_billing_cycle(self, tenant_id: str) -> Optional[Invoice]:
        """Process billing cycle for tenant."""
        subscription = self.get_tenant_subscription(tenant_id)
        if not subscription:
            return None
        
        # Get usage
        usage = self.usage_tracker.get_tenant_usage_this_month(tenant_id)
        
        # Calculate overages
        quotas = {
            UsageMetricType.API_CALLS.value: 100000,
            UsageMetricType.STORAGE_GB.value: 50
        }
        
        overages = self.calculator.calculate_overage_charges(
            usage,
            subscription.plan,
            quotas
        )
        
        # Generate invoice
        invoice = self.invoice_generator.generate_invoice(
            subscription,
            overages,
            tax_rate=0.1
        )
        
        logger.info(f"Processed billing cycle for tenant {tenant_id} - Invoice: {invoice.invoice_id}")
        return invoice
    
    def get_billing_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get billing summary for tenant."""
        subscription = self.get_tenant_subscription(tenant_id)
        if not subscription:
            return {}
        
        usage = self.usage_tracker.get_tenant_usage_this_month(tenant_id)
        invoices = self.invoice_generator.get_tenant_invoices(tenant_id)
        events = self.event_logger.get_tenant_events(tenant_id)
        
        return {
            "subscription": {
                "plan": subscription.plan.value,
                "billing_cycle_start": subscription.billing_cycle_start.isoformat(),
                "billing_cycle_end": subscription.billing_cycle_end.isoformat()
            },
            "current_usage": usage,
            "invoices": [
                {
                    "invoice_id": inv.invoice_id,
                    "total_amount": inv.total_amount,
                    "status": inv.status,
                    "issued_at": inv.issued_at.isoformat() if inv.issued_at else None
                }
                for inv in invoices[-12:]  # Last 12 invoices
            ],
            "recent_events": [
                {
                    "event_type": evt.event_type,
                    "quantity": evt.quantity,
                    "cost": evt.total_cost,
                    "timestamp": evt.timestamp.isoformat()
                }
                for evt in events[:20]  # Last 20 events
            ]
        }
