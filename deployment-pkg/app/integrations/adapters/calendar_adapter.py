"""
Calendar service adapter wrapping GoogleCalendarService.
Provides unified error handling, retry logic, and rate limiting for Google Calendar.
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.services.calendar_service import get_google_calendar_service, GoogleCalendarService
from .base_adapter import BaseAdapter, AdapterRequest, AdapterResponse
from .errors import (
    AdapterError,
    ErrorCategory,
    ProviderConnectionError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderValidationError,
    ProviderNotFoundError,
)
from .retry_policy import ProviderRetryConfig, MODERATE_RETRY
from .rate_limiter import RateLimitConfig, CALENDAR_RATE_LIMIT


logger = logging.getLogger(__name__)


class CalendarAdapter(BaseAdapter):
    """
    Adapter for Google Calendar service.
    
    Handles:
    - Event creation, update, deletion
    - Availability slot finding
    - Rate limiting (10 req/s)
    - Retry logic with exponential backoff
    - Error categorization and logging
    - OAuth token handling
    """
    
    def __init__(
        self,
        calendar_service: Optional[GoogleCalendarService] = None,
        retry_config: Optional[ProviderRetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
    ):
        """
        Initialize calendar adapter.
        
        Args:
            calendar_service: GoogleCalendarService instance
            retry_config: Retry configuration
            rate_limit_config: Rate limit configuration
        """
        self.calendar_service = calendar_service or get_google_calendar_service()
        
        # Moderate retry for calendar operations
        if retry_config is None:
            retry_config = ProviderRetryConfig(default=MODERATE_RETRY)
        
        # Use Google Calendar rate limit
        if rate_limit_config is None:
            rate_limit_config = CALENDAR_RATE_LIMIT
        
        super().__init__(
            provider_name="calendar_google",
            retry_config=retry_config,
            rate_limit_config=rate_limit_config,
        )
    
    async def health_check(self) -> bool:
        """
        Check Google Calendar service health.
        
        Tests connectivity via API configuration check.
        
        Returns:
            True if service is healthy
        """
        try:
            # Check if calendar service is properly configured
            return self.calendar_service.headers is not None and bool(
                self.calendar_service.headers.get("Authorization")
            )
        except Exception as e:
            logger.error(f"Calendar health check failed: {e}")
            return False
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """
        Execute calendar operation.
        
        Supported operations:
        - create_event: Create new event
        - find_available_slots: Find available time slots
        - update_event: Update event
        - delete_event: Delete event
        """
        operation = request.operation
        
        try:
            if operation == "create_event":
                return await self._create_event(request)
            
            elif operation == "find_available_slots":
                return await self._find_available_slots(request)
            
            elif operation == "update_event":
                return await self._update_event(request)
            
            elif operation == "delete_event":
                return await self._delete_event(request)
            
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
        
        except AdapterError as e:
            return AdapterResponse(
                success=False,
                data=None,
                error=e,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            logger.error(f"Unexpected error in calendar adapter: {e}", exc_info=True)
            error = AdapterError(
                provider=self.provider_name,
                operation=operation,
                category=ErrorCategory.UNKNOWN,
                message=f"Unexpected error: {str(e)}",
                correlation_id=request.correlation_id,
                original_error=e,
            )
            return AdapterResponse(
                success=False,
                data=None,
                error=error,
                correlation_id=request.correlation_id,
            )
    
    async def _create_event(self, request: AdapterRequest) -> AdapterResponse:
        """Handle create_event operation."""
        params = request.parameters
        
        required = ["oauth_token", "title", "start_time", "end_time"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="create_event",
                message=f"Missing required: {missing}",
            )
        
        try:
            result = await self.calendar_service.create_event(
                oauth_token=params["oauth_token"],
                title=params["title"],
                start_time=params["start_time"],
                end_time=params["end_time"],
                description=params.get("description"),
                location=params.get("location"),
                attendees=params.get("attendees", []),
                send_updates=params.get("send_updates", "syncFail"),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_calendar_error(e, "create_event", request)
    
    async def _find_available_slots(self, request: AdapterRequest) -> AdapterResponse:
        """Handle find_available_slots operation."""
        params = request.parameters
        
        required = ["oauth_token", "start_time", "end_time", "duration_minutes"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="find_available_slots",
                message=f"Missing required: {missing}",
            )
        
        try:
            result = await self.calendar_service.find_available_slots(
                oauth_token=params["oauth_token"],
                start_time=params["start_time"],
                end_time=params["end_time"],
                duration_minutes=params["duration_minutes"],
                attendee_emails=params.get("attendee_emails", []),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_calendar_error(e, "find_available_slots", request)
    
    async def _update_event(self, request: AdapterRequest) -> AdapterResponse:
        """Handle update_event operation."""
        params = request.parameters
        
        required = ["oauth_token", "event_id"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="update_event",
                message=f"Missing required: {missing}",
            )
        
        try:
            result = await self.calendar_service.update_event(
                oauth_token=params["oauth_token"],
                event_id=params["event_id"],
                title=params.get("title"),
                start_time=params.get("start_time"),
                end_time=params.get("end_time"),
                description=params.get("description"),
                location=params.get("location"),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_calendar_error(e, "update_event", request)
    
    async def _delete_event(self, request: AdapterRequest) -> AdapterResponse:
        """Handle delete_event operation."""
        params = request.parameters
        
        required = ["oauth_token", "event_id"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="delete_event",
                message=f"Missing required: {missing}",
            )
        
        try:
            await self.calendar_service.delete_event(
                oauth_token=params["oauth_token"],
                event_id=params["event_id"],
            )
            
            return AdapterResponse(
                success=True,
                data={"deleted": True},
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_calendar_error(e, "delete_event", request)
    
    def _map_calendar_error(
        self,
        exc: Exception,
        operation: str,
        request: AdapterRequest,
    ) -> AdapterError:
        """Map calendar service exceptions to adapter errors."""
        
        # Connection errors
        if isinstance(exc, (ConnectionError, OSError)):
            return ProviderConnectionError(
                provider=self.provider_name,
                message=f"Failed to connect to Google Calendar: {str(exc)}",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Authentication errors
        if "401" in str(exc) or "unauthorized" in str(exc).lower():
            return ProviderAuthError(
                provider=self.provider_name,
                message="Google Calendar authentication failed",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Rate limiting
        if "429" in str(exc) or "rate" in str(exc).lower():
            return ProviderRateLimitError(
                provider=self.provider_name,
                message="Google Calendar rate limited",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Not found
        if "404" in str(exc) or "not found" in str(exc).lower():
            return ProviderNotFoundError(
                provider=self.provider_name,
                operation=operation,
                resource_id="event",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Default
        return AdapterError(
            provider=self.provider_name,
            operation=operation,
            category=ErrorCategory.UNKNOWN,
            message=f"Google Calendar error: {str(exc)}",
            original_error=exc,
            correlation_id=request.correlation_id,
        )


# Global calendar adapter instance
_calendar_adapter: Optional[CalendarAdapter] = None


def get_calendar_adapter() -> CalendarAdapter:
    """Get or create global calendar adapter."""
    global _calendar_adapter
    if _calendar_adapter is None:
        _calendar_adapter = CalendarAdapter()
    return _calendar_adapter
