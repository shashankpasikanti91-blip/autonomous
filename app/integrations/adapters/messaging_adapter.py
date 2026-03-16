"""
Messaging service adapter wrapping WhatsAppService.
Provides unified error handling, retry logic, and rate limiting for WhatsApp.
"""
from typing import Optional, Dict, Any
import logging

from app.services.messaging_service import get_whatsapp_service, WhatsAppService
from .base_adapter import BaseAdapter, AdapterRequest, AdapterResponse
from .errors import (
    AdapterError,
    ErrorCategory,
    ProviderConnectionError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderValidationError,
)
from .retry_policy import ProviderRetryConfig, MODERATE_RETRY
from .rate_limiter import RateLimitConfig, WHATSAPP_RATE_LIMIT


logger = logging.getLogger(__name__)


class MessagingAdapter(BaseAdapter):
    """
    Adapter for WhatsApp messaging service.
    
    Handles:
    - Text message sending
    - Template message sending
    - Media uploads
    - Message status tracking
    - Rate limiting (10 req/s)
    - Retry logic
    """
    
    def __init__(
        self,
        messaging_service: Optional[WhatsAppService] = None,
        retry_config: Optional[ProviderRetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
    ):
        """
        Initialize messaging adapter.
        
        Args:
            messaging_service: WhatsAppService instance
            retry_config: Retry configuration
            rate_limit_config: Rate limit configuration
        """
        self.messaging_service = messaging_service or get_whatsapp_service()
        
        # Moderate retry for messaging operations
        if retry_config is None:
            retry_config = ProviderRetryConfig(default=MODERATE_RETRY)
        
        # Use WhatsApp rate limit
        if rate_limit_config is None:
            rate_limit_config = WHATSAPP_RATE_LIMIT
        
        super().__init__(
            provider_name="messaging_whatsapp",
            retry_config=retry_config,
            rate_limit_config=rate_limit_config,
        )
    
    async def health_check(self) -> bool:
        """
        Check WhatsApp service health.
        
        Tests configuration and connectivity.
        
        Returns:
            True if service is healthy
        """
        try:
            # Check if service has required configuration
            return (
                self.messaging_service.api_token is not None and
                self.messaging_service.business_account_id is not None
            )
        except Exception as e:
            logger.error(f"WhatsApp health check failed: {e}")
            return False
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """
        Execute messaging operation.
        
        Supported operations:
        - send_message: Send single text message
        - send_template_message: Send template message
        - get_message_status: Get message delivery status
        - upload_media: Upload media file
        """
        operation = request.operation
        
        try:
            if operation == "send_message":
                return await self._send_message(request)
            
            elif operation == "send_template_message":
                return await self._send_template_message(request)
            
            elif operation == "get_message_status":
                return await self._get_message_status(request)
            
            elif operation == "upload_media":
                return await self._upload_media(request)
            
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
            logger.error(f"Unexpected error in messaging adapter: {e}", exc_info=True)
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
    
    async def _send_message(self, request: AdapterRequest) -> AdapterResponse:
        """Handle send_message operation."""
        params = request.parameters
        
        required = ["phone_number", "message"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="send_message",
                message=f"Missing required: {missing}",
            )
        
        try:
            result = await self.messaging_service.send_message(
                phone_number=params["phone_number"],
                message=params["message"],
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_messaging_error(e, "send_message", request)
    
    async def _send_template_message(self, request: AdapterRequest) -> AdapterResponse:
        """Handle send_template_message operation."""
        params = request.parameters
        
        required = ["phone_number", "template_name"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="send_template_message",
                message=f"Missing required: {missing}",
            )
        
        try:
            result = await self.messaging_service.send_template_message(
                phone_number=params["phone_number"],
                template_name=params["template_name"],
                variables=params.get("variables", []),
                language_code=params.get("language_code", "en"),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_messaging_error(e, "send_template_message", request)
    
    async def _get_message_status(self, request: AdapterRequest) -> AdapterResponse:
        """Handle get_message_status operation."""
        params = request.parameters
        
        if "message_id" not in params:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="get_message_status",
                message="message_id required",
            )
        
        try:
            result = await self.messaging_service.get_message_status(
                message_id=params["message_id"],
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_messaging_error(e, "get_message_status", request)
    
    async def _upload_media(self, request: AdapterRequest) -> AdapterResponse:
        """Handle upload_media operation."""
        params = request.parameters
        
        required = ["file_path", "media_type"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="upload_media",
                message=f"Missing required: {missing}",
            )
        
        try:
            result = await self.messaging_service.upload_media(
                file_path=params["file_path"],
                media_type=params["media_type"],
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        except Exception as e:
            raise self._map_messaging_error(e, "upload_media", request)
    
    def _map_messaging_error(
        self,
        exc: Exception,
        operation: str,
        request: AdapterRequest,
    ) -> AdapterError:
        """Map messaging service exceptions to adapter errors."""
        
        # Connection errors
        if isinstance(exc, (ConnectionError, OSError)):
            return ProviderConnectionError(
                provider=self.provider_name,
                message=f"Failed to connect to WhatsApp: {str(exc)}",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Authentication errors
        if "401" in str(exc) or "unauthorized" in str(exc).lower():
            return ProviderAuthError(
                provider=self.provider_name,
                message="WhatsApp authentication failed",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Rate limiting
        if "429" in str(exc) or "rate" in str(exc).lower():
            return ProviderRateLimitError(
                provider=self.provider_name,
                message="WhatsApp rate limited",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Validation errors
        if isinstance(exc, ValueError):
            return ProviderValidationError(
                provider=self.provider_name,
                operation=operation,
                message=str(exc),
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Default
        return AdapterError(
            provider=self.provider_name,
            operation=operation,
            category=ErrorCategory.UNKNOWN,
            message=f"WhatsApp error: {str(exc)}",
            original_error=exc,
            correlation_id=request.correlation_id,
        )


# Global messaging adapter instance
_messaging_adapter: Optional[MessagingAdapter] = None


def get_messaging_adapter() -> MessagingAdapter:
    """Get or create global messaging adapter."""
    global _messaging_adapter
    if _messaging_adapter is None:
        _messaging_adapter = MessagingAdapter()
    return _messaging_adapter
