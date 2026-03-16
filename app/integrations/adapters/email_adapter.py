"""
Email service adapter wrapping EmailService.
Provides unified error handling, retry logic, and rate limiting for email providers.
"""
from typing import Optional, Dict, Any
import logging

from app.services.email_service import get_email_service, EmailService
from .base_adapter import BaseAdapter, AdapterRequest, AdapterResponse
from .errors import (
    AdapterError,
    ErrorCategory,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderAuthError,
    ProviderValidationError,
    map_http_status_to_error,
)
from .retry_policy import ProviderRetryConfig, MODERATE_RETRY
from .rate_limiter import RateLimitConfig, GMAIL_RATE_LIMIT


logger = logging.getLogger(__name__)


class EmailAdapter(BaseAdapter):
    """
    Adapter for email service with multiple providers (Gmail, SendGrid, SMTP).
    
    Handles:
    - Provider selection and fallback
    - Rate limiting across providers
    - Retry logic with exponential backoff
    - Error categorization and logging
    - Health monitoring
    """
    
    def __init__(
        self,
        email_service: Optional[EmailService] = None,
        retry_config: Optional[ProviderRetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
    ):
        """
        Initialize email adapter.
        
        Args:
            email_service: EmailService instance (gets singleton if not provided)
            retry_config: Retry configuration
            rate_limit_config: Rate limit configuration
        """
        self.email_service = email_service or get_email_service()
        
        # Use moderate retry for email, with specific operation overrides
        if retry_config is None:
            retry_config = ProviderRetryConfig(
                default=MODERATE_RETRY,
                overrides={
                    "send_batch_emails": MODERATE_RETRY,  # Retry batches
                }
            )
        
        # Use Gmail rate limit as baseline
        if rate_limit_config is None:
            rate_limit_config = GMAIL_RATE_LIMIT
        
        super().__init__(
            provider_name="email",
            retry_config=retry_config,
            rate_limit_config=rate_limit_config,
        )
    
    async def health_check(self) -> bool:
        """
        Check email service health.
        
        Tests connectivity by verifying service configuration.
        
        Returns:
            True if service is healthy
        """
        try:
            # If SMTP configured, try connection
            if self.email_service.smtp_config:
                # Could test SMTP connection here
                # For now, just verify config exists
                return bool(self.email_service.smtp_config)
            
            # Gmail or SendGrid configured
            return bool(
                self.email_service.gmail_config or
                self.email_service.sendgrid_config
            )
        except Exception as e:
            logger.error(f"Email health check failed: {e}")
            return False
    
    async def execute_operation(
        self,
        request: AdapterRequest
    ) -> AdapterResponse:
        """
        Execute email operation.
        
        Supported operations:
        - send_email: Send single email
        - send_batch_emails: Send multiple emails with template
        """
        operation = request.operation
        params = request.parameters
        
        try:
            if operation == "send_email":
                return await self._send_email(request)
            
            elif operation == "send_batch_emails":
                return await self._send_batch_emails(request)
            
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
            logger.error(f"Unexpected error in email adapter: {e}", exc_info=True)
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
    
    async def _send_email(self, request: AdapterRequest) -> AdapterResponse:
        """Handle send_email operation."""
        params = request.parameters
        
        # Validate required parameters
        required = ["to_address", "subject", "body_html"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="send_email",
                message=f"Missing required parameters: {missing}",
            )
        
        try:
            result = await self.email_service.send_email(
                to_address=params["to_address"],
                subject=params["subject"],
                body_html=params["body_html"],
                body_text=params.get("body_text"),
                from_name=params.get("from_name"),
                reply_to=params.get("reply_to"),
                oauth_token=params.get("oauth_token"),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        
        except Exception as e:
            # Map exception to error
            error = self._map_email_error(e, "send_email", request)
            raise error
    
    async def _send_batch_emails(self, request: AdapterRequest) -> AdapterResponse:
        """Handle send_batch_emails operation."""
        params = request.parameters
        
        # Validate required parameters
        required = ["recipients", "template_subject", "template_body"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ProviderValidationError(
                provider=self.provider_name,
                operation="send_batch_emails",
                message=f"Missing required parameters: {missing}",
            )
        
        try:
            result = await self.email_service.send_batch_emails(
                recipients=params["recipients"],
                template_subject=params["template_subject"],
                template_body=params["template_body"],
                from_name=params.get("from_name"),
                oauth_token=params.get("oauth_token"),
            )
            
            return AdapterResponse(
                success=True,
                data=result,
                correlation_id=request.correlation_id,
            )
        
        except Exception as e:
            error = self._map_email_error(e, "send_batch_emails", request)
            raise error
    
    def _map_email_error(
        self,
        exc: Exception,
        operation: str,
        request: AdapterRequest,
    ) -> AdapterError:
        """Map email service exceptions to adapter errors."""
        
        # Connection errors
        if isinstance(exc, (ConnectionError, OSError)):
            return ProviderConnectionError(
                provider=self.provider_name,
                message=f"Failed to connect to email service: {str(exc)}",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Authentication errors
        if "401" in str(exc) or "unauthorized" in str(exc).lower():
            return ProviderAuthError(
                provider=self.provider_name,
                message="Email service authentication failed",
                original_error=exc,
                correlation_id=request.correlation_id,
            )
        
        # Rate limiting
        if "429" in str(exc) or "rate" in str(exc).lower():
            return ProviderRateLimitError(
                provider=self.provider_name,
                message="Email service rate limited",
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
        
        # Default: unknown error
        return AdapterError(
            provider=self.provider_name,
            operation=operation,
            category=ErrorCategory.UNKNOWN,
            message=f"Email service error: {str(exc)}",
            original_error=exc,
            correlation_id=request.correlation_id,
        )


# Global email adapter instance
_email_adapter: Optional[EmailAdapter] = None


def get_email_adapter() -> EmailAdapter:
    """Get or create global email adapter."""
    global _email_adapter
    if _email_adapter is None:
        _email_adapter = EmailAdapter()
    return _email_adapter
