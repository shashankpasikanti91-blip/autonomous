"""
Unified error model for all provider integrations.
Enables consistent error handling, logging, and retry decisions across adapters.
"""
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


class ErrorCategory(str, Enum):
    """Error classification for routing retry/fallback decisions."""
    AUTHENTICATION = "authentication"  # AuthError, OAuth failure, token expired
    AUTHORIZATION = "authorization"    # Permission denied, insufficient scopes
    RATE_LIMIT = "rate_limit"          # Too many requests, quota exceeded
    VALIDATION = "validation"          # Invalid input, bad request
    NOT_FOUND = "not_found"            # Resource doesn't exist
    CONFLICT = "conflict"              # Resource conflict, state mismatch
    TRANSIENT = "transient"            # Temporary error, safe to retry
    SERVICE_UNAVAILABLE = "unavailable" # Provider down (5xx, timeout)
    CONFIGURATION = "configuration"    # Config error, wrong credentials
    UNKNOWN = "unknown"                # Unmapped error


class ErrorSeverity(str, Enum):
    """Severity levels for error prioritization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AdapterError(Exception):
    """
    Unified error model for all provider adapters.
    
    Provides:
    - Consistent error handling across providers
    - Retry decision guidance
    - Correlation tracking
    - Error history for analytics
    """
    
    provider: str                          # Provider name (gmail, hubspot, etc)
    operation: str                         # Operation (send_email, create_contact)
    category: ErrorCategory                # Error classification
    message: str                           # Human-readable message
    
    status_code: Optional[int] = None      # HTTP status code if applicable
    original_error: Optional[Exception] = None  # Underlying error
    
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    is_retryable: bool = False             # Should adapter retry?
    
    correlation_id: Optional[str] = None   # Trace correlation
    request_data: Dict[str, Any] = field(default_factory=dict)  # Request context
    response_data: Dict[str, Any] = field(default_factory=dict) # Response context
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __str__(self) -> str:
        """Human-readable error string."""
        return f"{self.provider}.{self.operation}: {self.category.value} - {self.message}"
    
    def is_auth_error(self) -> bool:
        """Check if authentication/authorization error."""
        return self.category in (
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.CONFIGURATION
        )
    
    def is_transient(self) -> bool:
        """Check if error is transient (safe to retry)."""
        return self.category in (
            ErrorCategory.TRANSIENT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.SERVICE_UNAVAILABLE
        ) or self.is_retryable
    
    def should_fallback(self) -> bool:
        """Check if should attempt fallback to alternative provider."""
        return (
            self.is_transient() or
            self.category in (ErrorCategory.SERVICE_UNAVAILABLE, ErrorCategory.RATE_LIMIT)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/telemetry."""
        return {
            "provider": self.provider,
            "operation": self.operation,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "status_code": self.status_code,
            "is_retryable": self.is_retryable,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }


class ProviderConnectionError(AdapterError):
    """Connection failure to provider."""
    def __init__(self, provider: str, message: str, **kwargs):
        super().__init__(
            provider=provider,
            operation="connect",
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            message=message,
            is_retryable=True,
            **kwargs
        )


class ProviderAuthError(AdapterError):
    """Authentication/authorization failure."""
    def __init__(self, provider: str, message: str, category: ErrorCategory = None, **kwargs):
        super().__init__(
            provider=provider,
            operation="authenticate",
            category=category or ErrorCategory.AUTHENTICATION,
            message=message,
            severity=ErrorSeverity.HIGH,
            is_retryable=False,
            **kwargs
        )


class ProviderRateLimitError(AdapterError):
    """Rate limit exceeded."""
    def __init__(self, provider: str, message: str, retry_after: int = None, **kwargs):
        super().__init__(
            provider=provider,
            operation="rate_limit",
            category=ErrorCategory.RATE_LIMIT,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            is_retryable=True,
            **kwargs
        )
        self.retry_after = retry_after  # Seconds to wait before retry


class ProviderValidationError(AdapterError):
    """Invalid input or bad request."""
    def __init__(self, provider: str, operation: str, message: str, **kwargs):
        super().__init__(
            provider=provider,
            operation=operation,
            category=ErrorCategory.VALIDATION,
            message=message,
            severity=ErrorSeverity.LOW,
            is_retryable=False,
            **kwargs
        )


class ProviderNotFoundError(AdapterError):
    """Resource not found."""
    def __init__(self, provider: str, operation: str, resource_id: str, **kwargs):
        super().__init__(
            provider=provider,
            operation=operation,
            category=ErrorCategory.NOT_FOUND,
            message=f"Resource not found: {resource_id}",
            severity=ErrorSeverity.LOW,
            is_retryable=False,
            **kwargs
        )


class ProviderConflictError(AdapterError):
    """Resource conflict or state mismatch."""
    def __init__(self, provider: str, operation: str, message: str, **kwargs):
        super().__init__(
            provider=provider,
            operation=operation,
            category=ErrorCategory.CONFLICT,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            is_retryable=True,
            **kwargs
        )


class ProviderTimeoutError(AdapterError):
    """Operation timeout."""
    def __init__(self, provider: str, operation: str, timeout_seconds: float, **kwargs):
        super().__init__(
            provider=provider,
            operation=operation,
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            message=f"Operation timeout after {timeout_seconds}s",
            severity=ErrorSeverity.MEDIUM,
            is_retryable=True,
            **kwargs
        )
        self.timeout_seconds = timeout_seconds


def map_http_status_to_error(
    provider: str,
    operation: str,
    status_code: int,
    message: str,
    **kwargs
) -> AdapterError:
    """
    Map HTTP status code to appropriate error category and retryability.
    
    Args:
        provider: Provider name
        operation: Operation name
        status_code: HTTP status code
        message: Error message
        **kwargs: Additional error data
    
    Returns:
        AdapterError instance with appropriate category
    """
    # Authentication errors (4xx client errors related to auth)
    if status_code == 401:
        return ProviderAuthError(
            provider=provider,
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            status_code=status_code,
            **kwargs
        )
    elif status_code == 403:
        return ProviderAuthError(
            provider=provider,
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            status_code=status_code,
            **kwargs
        )
    
    # Rate limiting
    elif status_code == 429:
        retry_after = kwargs.pop("retry_after", None)
        return ProviderRateLimitError(
            provider=provider,
            message=message,
            retry_after=retry_after,
            status_code=status_code,
            **kwargs
        )
    
    # Validation errors (4xx excluding above)
    elif 400 <= status_code < 404:
        return ProviderValidationError(
            provider=provider,
            operation=operation,
            message=message,
            status_code=status_code,
            **kwargs
        )
    
    # Not found
    elif status_code == 404:
        return ProviderNotFoundError(
            provider=provider,
            operation=operation,
            resource_id=kwargs.pop("resource_id", "unknown"),
            status_code=status_code,
            **kwargs
        )
    
    # Conflict
    elif status_code == 409:
        return ProviderConflictError(
            provider=provider,
            operation=operation,
            message=message,
            status_code=status_code,
            **kwargs
        )
    
    # Service errors (5xx are transient)
    elif status_code >= 500:
        error = AdapterError(
            provider=provider,
            operation=operation,
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            message=message,
            status_code=status_code,
            severity=ErrorSeverity.HIGH if status_code == 503 else ErrorSeverity.MEDIUM,
            is_retryable=True,
            **kwargs
        )
        return error
    
    # Default
    else:
        return AdapterError(
            provider=provider,
            operation=operation,
            category=ErrorCategory.UNKNOWN,
            message=message,
            status_code=status_code,
            **kwargs
        )
