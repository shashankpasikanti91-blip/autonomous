"""
Provider adapters for external integrations.

Provides:
- Unified adapter pattern for all providers
- Consistent error handling and retries
- Rate limiting protection
- Health monitoring
- Fallback strategies
"""

from .errors import (
    AdapterError,
    ErrorCategory,
    ErrorSeverity,
    ProviderConnectionError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderValidationError,
    ProviderNotFoundError,
    ProviderConflictError,
    ProviderTimeoutError,
    map_http_status_to_error,
)

from .retry_policy import (
    RetryStrategy,
    RetryPolicy,
    ProviderRetryConfig,
    CONSERVATIVE_RETRY,
    MODERATE_RETRY,
    AGGRESSIVE_RETRY,
    VERY_AGGRESSIVE_RETRY,
)

from .rate_limiter import (
    TokenBucket,
    RateLimitConfig,
    RateLimiter,
    get_rate_limiter,
    GMAIL_RATE_LIMIT,
    SENDGRID_RATE_LIMIT,
    CALENDAR_RATE_LIMIT,
    HUBSPOT_RATE_LIMIT,
    WHATSAPP_RATE_LIMIT,
    DEFAULT_RATE_LIMIT,
)

from .base_adapter import (
    AdapterRequest,
    AdapterResponse,
    BaseAdapter,
)

__all__ = [
    # Errors
    "AdapterError",
    "ErrorCategory",
    "ErrorSeverity",
    "ProviderConnectionError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderValidationError",
    "ProviderNotFoundError",
    "ProviderConflictError",
    "ProviderTimeoutError",
    "map_http_status_to_error",
    
    # Retry
    "RetryStrategy",
    "RetryPolicy",
    "ProviderRetryConfig",
    "CONSERVATIVE_RETRY",
    "MODERATE_RETRY",
    "AGGRESSIVE_RETRY",
    "VERY_AGGRESSIVE_RETRY",
    
    # Rate limiting
    "TokenBucket",
    "RateLimitConfig",
    "RateLimiter",
    "get_rate_limiter",
    "GMAIL_RATE_LIMIT",
    "SENDGRID_RATE_LIMIT",
    "CALENDAR_RATE_LIMIT",
    "HUBSPOT_RATE_LIMIT",
    "WHATSAPP_RATE_LIMIT",
    "DEFAULT_RATE_LIMIT",
    
    # Base adapter
    "AdapterRequest",
    "AdapterResponse",
    "BaseAdapter",
]
