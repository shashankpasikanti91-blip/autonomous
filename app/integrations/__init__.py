"""
Integrations package with provider adapters, health monitoring, and resilience.

Core components:
- Adapters: Unified interface for all providers (email, messaging, calendar, CRM, etc)
- Health Monitoring: Periodic health checks, automatic fallback, degraded mode
- Credential Management: OAuth token lifecycle, refresh, rotation, expiration
- Sandbox Mode: Mock providers for testing without real credentials
- Integration Telemetry: Event tracking, metrics, reliability scoring
- Observability: Tracing, correlation IDs, error tracking
"""

# adapter pattern and error handling
from app.integrations.adapters import (
    BaseAdapter,
    AdapterRequest,
    AdapterResponse,
    AdapterError,
    ErrorCategory,
    ErrorSeverity,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderConnectionError,
    ProviderValidationError,
    ProviderNotFoundError,
    ProviderConflictError,
    ProviderTimeoutError,
    map_http_status_to_error,
    RetryPolicy,
    ProviderRetryConfig,
    RateLimitConfig,
    get_rate_limiter,
)

# Service adapters
from app.integrations.adapters.email_adapter import (
    EmailAdapter,
    get_email_adapter,
)
from app.integrations.adapters.crm_adapter import (
    CRMAdapter,
    get_crm_adapter,
)
from app.integrations.adapters.calendar_adapter import (
    CalendarAdapter,
    get_calendar_adapter,
)
from app.integrations.adapters.messaging_adapter import (
    MessagingAdapter,
    get_messaging_adapter,
)

# Health monitoring
from app.integrations.health_monitor import (
    HealthMonitor,
    ProviderHealthStatus,
    get_health_monitor,
    attempt_fallback,
)

# Credential management
from app.integrations.credential_manager import (
    Credential,
    CredentialManager,
    get_credential_manager,
)

# Sandbox/mock providers
from app.integrations.sandbox import (
    SandboxMode,
    SandboxConfig,
    get_sandbox_config,
    set_sandbox_mode,
    enable_sandbox_for_provider,
    disable_sandbox_for_provider,
    MockEmailProvider,
    MockWhatsAppProvider,
    MockGoogleCalendarProvider,
    MockHubSpotProvider,
    get_mock_email_provider,
    get_mock_whatsapp_provider,
    get_mock_calendar_provider,
    get_mock_hubspot_provider,
    reset_all_mocks,
    SandboxEmailAdapter,
    SandboxMessagingAdapter,
    SandboxCalendarAdapter,
    SandboxCRMAdapter,
    get_sandbox_email_adapter,
    get_sandbox_messaging_adapter,
    get_sandbox_calendar_adapter,
    get_sandbox_crm_adapter,
)

# Integration telemetry
from app.integrations.integration_telemetry import (
    IntegrationTelemetry,
    ProviderEvent,
    ProviderMetrics,
    EventType,
    get_integration_telemetry,
    record_provider_success,
    record_provider_failure,
)

# Legacy modules (Phase 3)
from app.integrations.firebase import (
    FirebaseClient, AuthenticationManager, FirestoreManager,
    RealtimeNotificationManager, StorageManager
)
from app.integrations.oauth_manager import (
    OAuthToken, GoogleOAuthManager, HubSpotOAuthManager, OAuthManager,
    get_oauth_manager
)
from app.integrations.persistence import (
    WorkflowExecution, FirestorePersistence, get_persistence
)

__all__ = [
    # Adapter pattern
    "BaseAdapter",
    "AdapterRequest",
    "AdapterResponse",
    "AdapterError",
    "ErrorCategory",
    "ErrorSeverity",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderConnectionError",
    "ProviderValidationError",
    "ProviderNotFoundError",
    "ProviderConflictError",
    "ProviderTimeoutError",
    "map_http_status_to_error",
    "RetryPolicy",
    "ProviderRetryConfig",
    "RateLimitConfig",
    "get_rate_limiter",
    
    # Service adapters
    "EmailAdapter",
    "get_email_adapter",
    "CRMAdapter",
    "get_crm_adapter",
    "CalendarAdapter",
    "get_calendar_adapter",
    "MessagingAdapter",
    "get_messaging_adapter",
    
    # Health monitoring
    "HealthMonitor",
    "ProviderHealthStatus",
    "get_health_monitor",
    "attempt_fallback",
    
    # Credential management
    "Credential",
    "CredentialManager",
    "get_credential_manager",
    
    # Sandbox
    "SandboxMode",
    "SandboxConfig",
    "get_sandbox_config",
    "set_sandbox_mode",
    "enable_sandbox_for_provider",
    "disable_sandbox_for_provider",
    "MockEmailProvider",
    "MockWhatsAppProvider",
    "MockGoogleCalendarProvider",
    "MockHubSpotProvider",
    "get_mock_email_provider",
    "get_mock_whatsapp_provider",
    "get_mock_calendar_provider",
    "get_mock_hubspot_provider",
    "reset_all_mocks",
    "SandboxEmailAdapter",
    "SandboxMessagingAdapter",
    "SandboxCalendarAdapter",
    "SandboxCRMAdapter",
    "get_sandbox_email_adapter",
    "get_sandbox_messaging_adapter",
    "get_sandbox_calendar_adapter",
    "get_sandbox_crm_adapter",
    
    # Integration telemetry
    "IntegrationTelemetry",
    "ProviderEvent",
    "ProviderMetrics",
    "EventType",
    "get_integration_telemetry",
    "record_provider_success",
    "record_provider_failure",
    
    # Legacy (Firebase, OAuth, Persistence)
    "FirebaseClient",
    "AuthenticationManager",
    "FirestoreManager",
    "RealtimeNotificationManager",
    "StorageManager",
    "OAuthToken",
    "GoogleOAuthManager",
    "HubSpotOAuthManager",
    "OAuthManager",
    "get_oauth_manager",
    "WorkflowExecution",
    "FirestorePersistence",
    "get_persistence",
]
