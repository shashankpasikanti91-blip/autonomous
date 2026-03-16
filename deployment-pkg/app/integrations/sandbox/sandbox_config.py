"""
Sandbox mode manager for switching between real and mock providers.
"""
from enum import Enum
from typing import Dict, Optional
import logging


logger = logging.getLogger(__name__)


class SandboxMode(str, Enum):
    """Sandbox mode options."""
    PRODUCTION = "production"  # Real providers only
    SANDBOX = "sandbox"        # Mock providers only
    HYBRID = "hybrid"          # Fallback from real to mock on error


class SandboxConfig:
    """Configuration for sandbox mode."""
    
    def __init__(self, mode: SandboxMode = SandboxMode.PRODUCTION):
        """
        Initialize sandbox config.
        
        Args:
            mode: Sandbox mode (production, sandbox, hybrid)
        """
        self.mode = mode
        self.enabled_sandboxes: Dict[str, bool] = {}  # Per-provider enable/disable
    
    def is_production(self) -> bool:
        """Check if in production mode."""
        return self.mode == SandboxMode.PRODUCTION
    
    def is_sandbox(self) -> bool:
        """Check if in sandbox mode."""
        return self.mode == SandboxMode.SANDBOX
    
    def is_hybrid(self) -> bool:
        """Check if in hybrid mode."""
        return self.mode == SandboxMode.HYBRID
    
    def set_mode(self, mode: SandboxMode):
        """Set sandbox mode."""
        self.mode = mode
        logger.info(f"Sandbox mode changed to: {mode.value}")
    
    def enable_provider_sandbox(self, provider: str):
        """Enable sandbox for specific provider (even in production mode)."""
        self.enabled_sandboxes[provider] = True
        logger.info(f"Enabled sandbox for provider: {provider}")
    
    def disable_provider_sandbox(self, provider: str):
        """Disable sandbox for specific provider."""
        self.enabled_sandboxes[provider] = False
        logger.info(f"Disabled sandbox for provider: {provider}")
    
    def should_use_sandbox(self, provider: str) -> bool:
        """
        Determine if should use sandbox for provider.
        
        Args:
            provider: Provider name
        
        Returns:
            True if should use sandbox
        """
        # If explicitly enabled/disabled for provider, respect that
        if provider in self.enabled_sandboxes:
            return self.enabled_sandboxes[provider]
        
        # Otherwise follow global mode
        return self.is_sandbox()


# Global sandbox config
_sandbox_config: Optional[SandboxConfig] = None


def get_sandbox_config() -> SandboxConfig:
    """Get or create global sandbox configuration."""
    global _sandbox_config
    if _sandbox_config is None:
        _sandbox_config = SandboxConfig()
    return _sandbox_config


def set_sandbox_mode(mode: SandboxMode):
    """Set global sandbox mode."""
    config = get_sandbox_config()
    config.set_mode(mode)


def enable_sandbox_for_provider(provider: str):
    """Enable sandbox for specific provider."""
    config = get_sandbox_config()
    config.enable_provider_sandbox(provider)


def disable_sandbox_for_provider(provider: str):
    """Disable sandbox for specific provider."""
    config = get_sandbox_config()
    config.disable_provider_sandbox(provider)
