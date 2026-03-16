"""
Sandbox adapters wrapping mock providers with adapter interface.
Allows seamless switching between real and mock via configuration.
"""
from typing import Optional
import logging

from app.integrations.adapters import (
    BaseAdapter,
    AdapterRequest,
    AdapterResponse,
    ProviderValidationError,
)
from .mock_providers import (
    get_mock_email_provider,
    get_mock_whatsapp_provider, 
    get_mock_calendar_provider,
    get_mock_hubspot_provider,
)
from .sandbox_config import get_sandbox_config


logger = logging.getLogger(__name__)


class SandboxEmailAdapter(BaseAdapter):
    """Sandbox email adapter using mock provider."""
    
    def __init__(self):
        """Initialize sandbox email adapter."""
        self.mock_provider = get_mock_email_provider()
        super().__init__(provider_name="email_sandbox")
    
    async def health_check(self) -> bool:
        """Mock email is always healthy."""
        return True
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """Execute mock email operation."""
        operation = request.operation
        params = request.parameters
        
        try:
            if operation == "send_email":
                result = await self.mock_provider.send_email(
                    to_address=params.get("to_address"),
                    subject=params.get("subject"),
                    body_html=params.get("body_html"),
                    body_text=params.get("body_text"),
                    from_name=params.get("from_name"),
                    reply_to=params.get("reply_to"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "send_batch_emails":
                result = await self.mock_provider.send_batch_emails(
                    recipients=params.get("recipients"),
                    template_subject=params.get("template_subject"),
                    template_body=params.get("template_body"),
                    from_name=params.get("from_name"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            else:
                error = ProviderValidationError(
                    provider=self.provider_name,
                    operation=operation,
                    message=f"Unknown operation: {operation}",
                )
                return AdapterResponse(
                    success=False,
                    data=None,
                    error=error,
                    correlation_id=request.correlation_id,
                )
        
        except Exception as e:
            logger.error(f"Sandbox email error: {e}")
            raise


class SandboxMessagingAdapter(BaseAdapter):
    """Sandbox messaging adapter using mock provider."""
    
    def __init__(self):
        """Initialize sandbox messaging adapter."""
        self.mock_provider = get_mock_whatsapp_provider()
        super().__init__(provider_name="messaging_sandbox")
    
    async def health_check(self) -> bool:
        """Mock messaging is always healthy."""
        return True
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """Execute mock messaging operation."""
        operation = request.operation
        params = request.parameters
        
        try:
            if operation == "send_message":
                result = await self.mock_provider.send_message(
                    phone_number=params.get("phone_number"),
                    message=params.get("message"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "send_template_message":
                result = await self.mock_provider.send_template_message(
                    phone_number=params.get("phone_number"),
                    template_name=params.get("template_name"),
                    variables=params.get("variables"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "get_message_status":
                result = await self.mock_provider.get_message_status(
                    message_id=params.get("message_id"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            else:
                error = ProviderValidationError(
                    provider=self.provider_name,
                    operation=operation,
                    message=f"Unknown operation: {operation}",
                )
                return AdapterResponse(
                    success=False,
                    data=None,
                    error=error,
                    correlation_id=request.correlation_id,
                )
        
        except Exception as e:
            logger.error(f"Sandbox messaging error: {e}")
            raise


class SandboxCalendarAdapter(BaseAdapter):
    """Sandbox calendar adapter using mock provider."""
    
    def __init__(self):
        """Initialize sandbox calendar adapter."""
        self.mock_provider = get_mock_calendar_provider()
        super().__init__(provider_name="calendar_sandbox")
    
    async def health_check(self) -> bool:
        """Mock calendar is always healthy."""
        return True
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """Execute mock calendar operation."""
        operation = request.operation
        params = request.parameters
        
        try:
            if operation == "create_event":
                result = await self.mock_provider.create_event(
                    oauth_token=params.get("oauth_token"),
                    title=params.get("title"),
                    start_time=params.get("start_time"),
                    end_time=params.get("end_time"),
                    description=params.get("description"),
                    location=params.get("location"),
                    attendees=params.get("attendees"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "find_available_slots":
                result = await self.mock_provider.find_available_slots(
                    oauth_token=params.get("oauth_token"),
                    start_time=params.get("start_time"),
                    end_time=params.get("end_time"),
                    duration_minutes=params.get("duration_minutes"),
                    attendee_emails=params.get("attendee_emails"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "update_event":
                result = await self.mock_provider.update_event(
                    oauth_token=params.get("oauth_token"),
                    event_id=params.get("event_id"),
                    title=params.get("title"),
                    start_time=params.get("start_time"),
                    end_time=params.get("end_time"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "delete_event":
                await self.mock_provider.delete_event(
                    oauth_token=params.get("oauth_token"),
                    event_id=params.get("event_id"),
                )
                return AdapterResponse(
                    success=True,
                    data={"deleted": True},
                    correlation_id=request.correlation_id,
                )
            
            else:
                error = ProviderValidationError(
                    provider=self.provider_name,
                    operation=operation,
                    message=f"Unknown operation: {operation}",
                )
                return AdapterResponse(
                    success=False,
                    data=None,
                    error=error,
                    correlation_id=request.correlation_id,
                )
        
        except Exception as e:
            logger.error(f"Sandbox calendar error: {e}")
            raise


class SandboxCRMAdapter(BaseAdapter):
    """Sandbox CRM adapter using mock provider."""
    
    def __init__(self):
        """Initialize sandbox CRM adapter."""
        self.mock_provider = get_mock_hubspot_provider()
        super().__init__(provider_name="crm_sandbox")
    
    async def health_check(self) -> bool:
        """Mock CRM is always healthy."""
        return True
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """Execute mock CRM operation."""
        operation = request.operation
        params = request.parameters
        
        try:
            if operation == "create_contact":
                result = await self.mock_provider.create_contact(
                    email=params.get("email"),
                    first_name=params.get("first_name"),
                    last_name=params.get("last_name"),
                    phone=params.get("phone"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "get_contact":
                result = await self.mock_provider.get_contact(
                    contact_id=params.get("contact_id"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "update_contact":
                result = await self.mock_provider.update_contact(
                    contact_id=params.get("contact_id"),
                    **{k: v for k, v in params.items() if k != "contact_id"}
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "create_deal":
                result = await self.mock_provider.create_deal(
                    deal_name=params.get("deal_name"),
                    contact_id=params.get("contact_id"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "log_activity":
                result = await self.mock_provider.log_activity(
                    contact_id=params.get("contact_id"),
                    activity_type=params.get("activity_type"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            elif operation == "search_contacts":
                result = await self.mock_provider.search_contacts(
                    query=params.get("query"),
                )
                return AdapterResponse(
                    success=True,
                    data=result,
                    correlation_id=request.correlation_id,
                )
            
            else:
                error = ProviderValidationError(
                    provider=self.provider_name,
                    operation=operation,
                    message=f"Unknown operation: {operation}",
                )
                return AdapterResponse(
                    success=False,
                    data=None,
                    error=error,
                    correlation_id=request.correlation_id,
                )
        
        except Exception as e:
            logger.error(f"Sandbox CRM error: {e}")
            raise


# Global sandbox adapter instances
_sandbox_email: Optional[SandboxEmailAdapter] = None
_sandbox_messaging: Optional[SandboxMessagingAdapter] = None
_sandbox_calendar: Optional[SandboxCalendarAdapter] = None
_sandbox_crm: Optional[SandboxCRMAdapter] = None


def get_sandbox_email_adapter() -> SandboxEmailAdapter:
    """Get or create global sandbox email adapter."""
    global _sandbox_email
    if _sandbox_email is None:
        _sandbox_email = SandboxEmailAdapter()
    return _sandbox_email


def get_sandbox_messaging_adapter() -> SandboxMessagingAdapter:
    """Get or create global sandbox messaging adapter."""
    global _sandbox_messaging
    if _sandbox_messaging is None:
        _sandbox_messaging = SandboxMessagingAdapter()
    return _sandbox_messaging


def get_sandbox_calendar_adapter() -> SandboxCalendarAdapter:
    """Get or create global sandbox calendar adapter."""
    global _sandbox_calendar
    if _sandbox_calendar is None:
        _sandbox_calendar = SandboxCalendarAdapter()
    return _sandbox_calendar


def get_sandbox_crm_adapter() -> SandboxCRMAdapter:
    """Get or create global sandbox CRM adapter."""
    global _sandbox_crm
    if _sandbox_crm is None:
        _sandbox_crm = SandboxCRMAdapter()
    return _sandbox_crm
