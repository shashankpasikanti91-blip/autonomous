"""
Sandbox module for safe provider testing and development.

Provides:
- Mock implementations of all providers
- Sandbox configuration and switching
- Sandbox adapters with real adapter interface
"""

from .mock_providers import (
    MockEmailProvider,
    MockWhatsAppProvider,
    MockGoogleCalendarProvider,
    MockHubSpotProvider,
    get_mock_email_provider,
    get_mock_whatsapp_provider,
    get_mock_calendar_provider,
    get_mock_hubspot_provider,
    reset_all_mocks,
)

from .sandbox_config import (
    SandboxMode,
    SandboxConfig,
    get_sandbox_config,
    set_sandbox_mode,
    enable_sandbox_for_provider,
    disable_sandbox_for_provider,
)

from .sandbox_adapters import (
    SandboxEmailAdapter,
    SandboxMessagingAdapter,
    SandboxCalendarAdapter,
    SandboxCRMAdapter,
    get_sandbox_email_adapter,
    get_sandbox_messaging_adapter,
    get_sandbox_calendar_adapter,
    get_sandbox_crm_adapter,
)

__all__ = [
    # Mock providers
    "MockEmailProvider",
    "MockWhatsAppProvider",
    "MockGoogleCalendarProvider",
    "MockHubSpotProvider",
    "get_mock_email_provider",
    "get_mock_whatsapp_provider",
    "get_mock_calendar_provider",
    "get_mock_hubspot_provider",
    "reset_all_mocks",
    
    # Sandbox config
    "SandboxMode",
    "SandboxConfig",
    "get_sandbox_config",
    "set_sandbox_mode",
    "enable_sandbox_for_provider",
    "disable_sandbox_for_provider",
    
    # Sandbox adapters
    "SandboxEmailAdapter",
    "SandboxMessagingAdapter",
    "SandboxCalendarAdapter",
    "SandboxCRMAdapter",
    "get_sandbox_email_adapter",
    "get_sandbox_messaging_adapter",
    "get_sandbox_calendar_adapter",
    "get_sandbox_crm_adapter",
]
