"""
Service Connector Abstractions

Provides unified interfaces for external service integrations:
- Email services (Gmail, SendGrid, SMTP)
- Messaging (WhatsApp, SMS)
- Calendar scheduling
- Payroll systems
- Invoice generation
- CRM platforms
- Visa monitoring
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio
import json
from utils.logger import get_logger


logger = get_logger(__name__)


# ============================================================================
# Data Models for Service Responses
# ============================================================================

class ServiceProvider(str, Enum):
    """Supported service providers."""
    GMAIL = "gmail"
    SENDGRID = "sendgrid"
    SMTP = "smtp"
    WHATSAPP = "whatsapp"
    TWILIO_SMS = "twilio_sms"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    QUICKBOOKS = "quickbooks"
    FRESHBOOKS = "freshbooks"
    STRIPE = "stripe"
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"


@dataclass
class ServiceResult:
    """Result from service operation."""
    success: bool
    message: str
    data: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error
        }


# ============================================================================
# Email Service Connector
# ============================================================================

class EmailConnector(ABC):
    """Base class for email service connectors."""
    
    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[Dict[str, bytes]] = None
    ) -> ServiceResult:
        """Send email."""
        pass
    
    @abstractmethod
    async def send_batch_emails(
        self,
        recipients: List[Dict[str, str]],
        subject_template: str,
        body_template: str
    ) -> ServiceResult:
        """Send batch emails with template substitution."""
        pass


class GmailConnector(EmailConnector):
    """Gmail connector implementation."""
    
    def __init__(self, service_account_key: str, from_address: str):
        self.service_account_key = service_account_key
        self.from_address = from_address
        self.provider = ServiceProvider.GMAIL
        logger.info(f"Gmail connector initialized: {from_address}")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[Dict[str, bytes]] = None
    ) -> ServiceResult:
        """Send email via Gmail."""
        try:
            # TODO: Implement actual Gmail API integration
            # from google.oauth2.service_account import Credentials
            # from googleapiclient.discovery import build
            
            logger.info(f"[EMAIL] Sending email to {to} via Gmail")
            
            # Simulate API call
            await asyncio.sleep(0.5)
            
            return ServiceResult(
                success=True,
                message=f"Email sent to {to}",
                data={
                    "message_id": f"gmail_{hash(to)}",
                    "to": to,
                    "subject": subject,
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider": self.provider.value
                }
            )
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send email: {str(e)}")
            return ServiceResult(
                success=False,
                message=f"Failed to send email to {to}",
                data={},
                error=str(e)
            )
    
    async def send_batch_emails(
        self,
        recipients: List[Dict[str, str]],
        subject_template: str,
        body_template: str
    ) -> ServiceResult:
        """Send batch emails."""
        try:
            results = []
            for recipient in recipients:
                # Simple template substitution
                subject = subject_template.format(**recipient)
                body = body_template.format(**recipient)
                
                result = await self.send_email(
                    to=recipient["email"],
                    subject=subject,
                    body=body
                )
                results.append(result.to_dict())
            
            return ServiceResult(
                success=True,
                message=f"Sent {len(recipients)} batch emails",
                data={"results": results}
            )
        except Exception as e:
            logger.error(f"[EMAIL] Batch send failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Batch email sending failed",
                data={},
                error=str(e)
            )


# ============================================================================
# Messaging Service Connector (WhatsApp/SMS)
# ============================================================================

class MessagingConnector(ABC):
    """Base class for messaging service connectors."""
    
    @abstractmethod
    async def send_message(
        self,
        phone_number: str,
        message: str,
        message_type: str = "text"
    ) -> ServiceResult:
        """Send message to phone number."""
        pass
    
    @abstractmethod
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        variables: Dict[str, str]
    ) -> ServiceResult:
        """Send templated message."""
        pass


class WhatsAppConnector(MessagingConnector):
    """WhatsApp connector implementation."""
    
    def __init__(self, api_token: str, business_account_id: str):
        self.api_token = api_token
        self.business_account_id = business_account_id
        self.provider = ServiceProvider.WHATSAPP
        logger.info(f"WhatsApp connector initialized: {business_account_id}")
    
    async def send_message(
        self,
        phone_number: str,
        message: str,
        message_type: str = "text"
    ) -> ServiceResult:
        """Send message via WhatsApp."""
        try:
            # TODO: Implement actual WhatsApp Business API integration
            # https://developers.facebook.com/docs/whatsapp/cloud-api
            
            logger.info(f"[MESSAGING] Sending WhatsApp to {phone_number}")
            
            await asyncio.sleep(0.3)
            
            return ServiceResult(
                success=True,
                message=f"WhatsApp sent to {phone_number}",
                data={
                    "message_id": f"wa_{hash(phone_number)}",
                    "phone_number": phone_number,
                    "message_type": message_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider": self.provider.value
                }
            )
        except Exception as e:
            logger.error(f"[MESSAGING] WhatsApp send failed: {str(e)}")
            return ServiceResult(
                success=False,
                message=f"Failed to send WhatsApp to {phone_number}",
                data={},
                error=str(e)
            )
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        variables: Dict[str, str]
    ) -> ServiceResult:
        """Send templated WhatsApp message."""
        try:
            logger.info(f"[MESSAGING] Sending template '{template_name}' to {phone_number}")
            
            await asyncio.sleep(0.3)
            
            return ServiceResult(
                success=True,
                message=f"Template message sent to {phone_number}",
                data={
                    "message_id": f"wa_template_{hash(template_name)}",
                    "phone_number": phone_number,
                    "template": template_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider": self.provider.value
                }
            )
        except Exception as e:
            logger.error(f"[MESSAGING] Template send failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Template send failed",
                data={},
                error=str(e)
            )


# ============================================================================
# Calendar Service Connector
# ============================================================================

class CalendarConnector(ABC):
    """Base class for calendar service connectors."""
    
    @abstractmethod
    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        description: Optional[str] = None
    ) -> ServiceResult:
        """Create calendar event."""
        pass
    
    @abstractmethod
    async def find_available_slots(
        self,
        attendees: List[str],
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime
    ) -> ServiceResult:
        """Find available time slots."""
        pass


class GoogleCalendarConnector(CalendarConnector):
    """Google Calendar connector implementation."""
    
    def __init__(self, service_account_key: str):
        self.service_account_key = service_account_key
        self.provider = ServiceProvider.GOOGLE_CALENDAR
        logger.info("Google Calendar connector initialized")
    
    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        description: Optional[str] = None
    ) -> ServiceResult:
        """Create event in Google Calendar."""
        try:
            # TODO: Implement actual Google Calendar API integration
            # from google.oauth2.service_account import Credentials
            # from googleapiclient.discovery import build
            
            logger.info(f"[CALENDAR] Creating event '{title}' with {len(attendees)} attendees")
            
            await asyncio.sleep(0.5)
            
            return ServiceResult(
                success=True,
                message=f"Event created: {title}",
                data={
                    "event_id": f"cal_{hash(title)}",
                    "title": title,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "attendees": attendees,
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider": self.provider.value
                }
            )
        except Exception as e:
            logger.error(f"[CALENDAR] Event creation failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Event creation failed",
                data={},
                error=str(e)
            )
    
    async def find_available_slots(
        self,
        attendees: List[str],
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime
    ) -> ServiceResult:
        """Find available time slots."""
        try:
            logger.info(f"[CALENDAR] Finding slots for {len(attendees)} attendees")
            
            await asyncio.sleep(0.5)
            
            # Mock available slots
            available_slots = [
                {
                    "start": (datetime.utcnow()).isoformat(),
                    "end": (datetime.utcnow()).isoformat(),
                    "attendees_confirmed": len(attendees)
                }
            ]
            
            return ServiceResult(
                success=True,
                message=f"Found {len(available_slots)} available slots",
                data={
                    "slots": available_slots,
                    "attendees": attendees,
                    "duration_minutes": duration_minutes
                }
            )
        except Exception as e:
            logger.error(f"[CALENDAR] Slot finding failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Slot finding failed",
                data={},
                error=str(e)
            )


# ============================================================================
# Payroll Service Connector
# ============================================================================

class PayrollConnector(ABC):
    """Base class for payroll service connectors."""
    
    @abstractmethod
    async def calculate_payroll(
        self,
        employee_id: str,
        hourly_rate: float,
        hours_worked: float,
        deductions: Dict[str, float] = None
    ) -> ServiceResult:
        """Calculate employee payroll."""
        pass
    
    @abstractmethod
    async def process_payment(
        self,
        employee_id: str,
        amount: float,
        payment_method: str
    ) -> ServiceResult:
        """Process payment."""
        pass


class PayrollProcessor(PayrollConnector):
    """Generic payroll processor."""
    
    def __init__(self, tax_rate: float = 0.15, health_insurance: float = 200.0):
        self.tax_rate = tax_rate
        self.health_insurance = health_insurance
        self.provider = "payroll_processor"
        logger.info("Payroll processor initialized")
    
    async def calculate_payroll(
        self,
        employee_id: str,
        hourly_rate: float,
        hours_worked: float,
        deductions: Dict[str, float] = None
    ) -> ServiceResult:
        """Calculate payroll."""
        try:
            logger.info(f"[PAYROLL] Calculating for employee {employee_id}")
            
            gross_salary = hourly_rate * hours_worked
            taxes = gross_salary * self.tax_rate
            total_deductions = self.health_insurance
            
            if deductions:
                total_deductions += sum(deductions.values())
            
            net_salary = gross_salary - taxes - total_deductions
            
            return ServiceResult(
                success=True,
                message=f"Payroll calculated for {employee_id}",
                data={
                    "employee_id": employee_id,
                    "gross_salary": gross_salary,
                    "taxes": taxes,
                    "deductions": total_deductions,
                    "net_salary": net_salary,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[PAYROLL] Calculation failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Payroll calculation failed",
                data={},
                error=str(e)
            )
    
    async def process_payment(
        self,
        employee_id: str,
        amount: float,
        payment_method: str
    ) -> ServiceResult:
        """Process payment."""
        try:
            logger.info(f"[PAYROLL] Processing payment for {employee_id}")
            
            await asyncio.sleep(0.3)
            
            return ServiceResult(
                success=True,
                message=f"Payment processed for {employee_id}",
                data={
                    "employee_id": employee_id,
                    "amount": amount,
                    "payment_method": payment_method,
                    "transaction_id": f"txn_{hash(employee_id)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[PAYROLL] Payment failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Payment processing failed",
                data={},
                error=str(e)
            )


# ============================================================================
# Invoice Service Connector
# ============================================================================

class InvoiceConnector(ABC):
    """Base class for invoice service connectors."""
    
    @abstractmethod
    async def generate_invoice(
        self,
        client_name: str,
        items: List[Dict[str, Any]],
        amount_due: float,
        due_date: datetime
    ) -> ServiceResult:
        """Generate invoice."""
        pass
    
    @abstractmethod
    async def send_invoice(
        self,
        invoice_id: str,
        recipient_email: str
    ) -> ServiceResult:
        """Send invoice to recipient."""
        pass


class InvoiceGenerator(InvoiceConnector):
    """Generic invoice generator."""
    
    def __init__(self, business_name: str, tax_id: str):
        self.business_name = business_name
        self.tax_id = tax_id
        self.provider = "invoice_generator"
        logger.info(f"Invoice generator initialized: {business_name}")
    
    async def generate_invoice(
        self,
        client_name: str,
        items: List[Dict[str, Any]],
        amount_due: float,
        due_date: datetime
    ) -> ServiceResult:
        """Generate invoice."""
        try:
            logger.info(f"[INVOICE] Generating invoice for {client_name}")
            
            invoice_number = f"INV-{hash(client_name) % 10000}"
            subtotal = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in items)
            tax = subtotal * 0.1  # 10% tax
            total = subtotal + tax
            
            return ServiceResult(
                success=True,
                message=f"Invoice generated: {invoice_number}",
                data={
                    "invoice_id": invoice_number,
                    "business_name": self.business_name,
                    "client_name": client_name,
                    "items": items,
                    "subtotal": subtotal,
                    "tax": tax,
                    "total": total,
                    "due_date": due_date.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[INVOICE] Generation failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Invoice generation failed",
                data={},
                error=str(e)
            )
    
    async def send_invoice(
        self,
        invoice_id: str,
        recipient_email: str
    ) -> ServiceResult:
        """Send invoice."""
        try:
            logger.info(f"[INVOICE] Sending invoice {invoice_id} to {recipient_email}")
            
            await asyncio.sleep(0.3)
            
            return ServiceResult(
                success=True,
                message=f"Invoice sent to {recipient_email}",
                data={
                    "invoice_id": invoice_id,
                    "recipient_email": recipient_email,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[INVOICE] Send failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Invoice send failed",
                data={},
                error=str(e)
            )


# ============================================================================
# CRM Service Connector
# ============================================================================

class CRMConnector(ABC):
    """Base class for CRM service connectors."""
    
    @abstractmethod
    async def create_lead(
        self,
        name: str,
        email: str,
        phone: str,
        company: str,
        source: str
    ) -> ServiceResult:
        """Create new lead."""
        pass
    
    @abstractmethod
    async def update_lead_status(
        self,
        lead_id: str,
        status: str
    ) -> ServiceResult:
        """Update lead status."""
        pass


class HubSpotConnector(CRMConnector):
    """HubSpot CRM connector."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider = ServiceProvider.HUBSPOT
        logger.info("HubSpot connector initialized")
    
    async def create_lead(
        self,
        name: str,
        email: str,
        phone: str,
        company: str,
        source: str
    ) -> ServiceResult:
        """Create lead in HubSpot."""
        try:
            # TODO: Integrate with actual HubSpot API
            # https://developers.hubspot.com/docs/api/crm/objects/contacts
            
            logger.info(f"[CRM] Creating lead: {name} ({email})")
            
            await asyncio.sleep(0.3)
            
            return ServiceResult(
                success=True,
                message=f"Lead created: {name}",
                data={
                    "lead_id": f"hs_lead_{hash(email)}",
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "company": company,
                    "source": source,
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider": self.provider.value
                }
            )
        except Exception as e:
            logger.error(f"[CRM] Lead creation failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Lead creation failed",
                data={},
                error=str(e)
            )
    
    async def update_lead_status(
        self,
        lead_id: str,
        status: str
    ) -> ServiceResult:
        """Update lead status."""
        try:
            logger.info(f"[CRM] Updating lead {lead_id} status to {status}")
            
            await asyncio.sleep(0.2)
            
            return ServiceResult(
                success=True,
                message=f"Lead {lead_id} status updated",
                data={
                    "lead_id": lead_id,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[CRM] Status update failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Status update failed",
                data={},
                error=str(e)
            )


# ============================================================================
# Visa Status Monitoring Connector
# ============================================================================

class VisaMonitoringConnector(ABC):
    """Base class for visa monitoring connectors."""
    
    @abstractmethod
    async def check_visa_status(
        self,
        employee_id: str,
        passport_number: str
    ) -> ServiceResult:
        """Check visa status."""
        pass
    
    @abstractmethod
    async def schedule_renewal_reminder(
        self,
        employee_id: str,
        expiry_date: datetime
    ) -> ServiceResult:
        """Schedule visa renewal reminder."""
        pass


class VisaMonitor(VisaMonitoringConnector):
    """Visa status monitoring service."""
    
    def __init__(self, api_endpoint: str):
        self.api_endpoint = api_endpoint
        self.provider = "visa_monitor"
        logger.info("Visa monitor initialized")
    
    async def check_visa_status(
        self,
        employee_id: str,
        passport_number: str
    ) -> ServiceResult:
        """Check visa status."""
        try:
            logger.info(f"[VISA] Checking status for {employee_id}")
            
            # TODO: Integrate with actual visa status checking API
            # This could be based on government APIs or third-party services
            
            await asyncio.sleep(0.4)
            
            return ServiceResult(
                success=True,
                message=f"Visa status retrieved for {employee_id}",
                data={
                    "employee_id": employee_id,
                    "passport_number": passport_number,
                    "visa_status": "valid",
                    "expiry_date": "2026-12-31",
                    "days_until_expiry": 310,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[VISA] Status check failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Visa status check failed",
                data={},
                error=str(e)
            )
    
    async def schedule_renewal_reminder(
        self,
        employee_id: str,
        expiry_date: datetime
    ) -> ServiceResult:
        """Schedule renewal reminder."""
        try:
            logger.info(f"[VISA] Scheduling reminder for {employee_id}")
            
            await asyncio.sleep(0.2)
            
            return ServiceResult(
                success=True,
                message=f"Renewal reminder scheduled for {employee_id}",
                data={
                    "employee_id": employee_id,
                    "expiry_date": expiry_date.isoformat(),
                    "reminder_date": (datetime.utcnow()).isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[VISA] Reminder scheduling failed: {str(e)}")
            return ServiceResult(
                success=False,
                message="Reminder scheduling failed",
                data={},
                error=str(e)
            )


# ============================================================================
# Service Connector Factory
# ============================================================================

class ServiceConnectorFactory:
    """Factory for creating service connectors."""
    
    def __init__(self):
        self.connectors: Dict[str, Any] = {}
    
    def register_connector(self, name: str, connector: Any) -> None:
        """Register a connector."""
        self.connectors[name] = connector
        logger.info(f"Connector registered: {name}")
    
    def get_connector(self, name: str) -> Optional[Any]:
        """Get a connector by name."""
        return self.connectors.get(name)
    
    def list_connectors(self) -> List[str]:
        """List all registered connectors."""
        return list(self.connectors.keys())


# ============================================================================
# Global Service Factory (Initialize in config)
# ============================================================================

service_factory = ServiceConnectorFactory()
