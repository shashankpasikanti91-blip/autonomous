"""
Provider health monitoring system.
Periodic health checks, automatic fallback strategy, and degraded mode handling.
"""
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging

from .adapters import BaseAdapter


logger = logging.getLogger(__name__)


@dataclass
class ProviderHealthStatus:
    """Health status for a provider."""
    provider_name: str
    is_healthy: bool
    is_degraded: bool
    last_check: Optional[datetime]
    consecutive_failures: int
    failure_rate: float  # 0.0 to 1.0
    status_message: str = ""


class HealthMonitor:
    """
    Monitors health of all provider adapters.
    
    Provides:
    - Periodic health checks
    - Automatic fallback strategy
    - Degraded mode detection
    - Health status reporting
    """
    
    def __init__(
        self,
        check_interval_seconds: int = 60,
        failure_threshold: int = 3,
        recovery_interval_seconds: int = 300,
    ):
        """
        Initialize health monitor.
        
        Args:
            check_interval_seconds: How often to check provider health
            failure_threshold: Consecutive failures before marking degraded
            recovery_interval_seconds: How often to attempt recovery of degraded providers
        """
        self.check_interval_seconds = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.recovery_interval_seconds = recovery_interval_seconds
        
        self.adapters: Dict[str, BaseAdapter] = {}
        self.health_status: Dict[str, ProviderHealthStatus] = {}
        self.is_running = False
        self.last_recovery_attempt: Dict[str, datetime] = {}
        
        # Callbacks
        self.on_provider_recovered: Optional[Callable] = None
        self.on_provider_degraded: Optional[Callable] = None
        self.on_provider_failed: Optional[Callable] = None
    
    def register_adapter(self, adapter: BaseAdapter):
        """Register adapter for health monitoring."""
        self.adapters[adapter.provider_name] = adapter
        logger.info(f"Registered adapter for monitoring: {adapter.provider_name}")
    
    def unregister_adapter(self, provider_name: str):
        """Unregister adapter from monitoring."""
        self.adapters.pop(provider_name, None)
        self.health_status.pop(provider_name, None)
    
    async def start(self):
        """Start health monitoring loop."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Health monitor started")
        
        try:
            await self._monitor_loop()
        except Exception as e:
            logger.error(f"Health monitor error: {e}", exc_info=True)
            self.is_running = False
    
    def stop(self):
        """Stop health monitoring loop."""
        self.is_running = False
        logger.info("Health monitor stopped")
    
    async def _monitor_loop(self):
        """Main health monitoring loop."""
        while self.is_running:
            try:
                # Check all adapters
                for provider_name, adapter in self.adapters.items():
                    try:
                        is_healthy = await adapter.check_health()
                        self._update_health_status(provider_name, adapter, is_healthy)
                    except Exception as e:
                        logger.error(f"Health check error for {provider_name}: {e}")
                        self._update_health_status(provider_name, adapter, False)
                
                # Sleep before next check
                await asyncio.sleep(self.check_interval_seconds)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Brief pause before retry
    
    def _update_health_status(
        self,
        provider_name: str,
        adapter: BaseAdapter,
        is_healthy: bool,
    ):
        """Update health status for provider."""
        was_healthy = provider_name in self.health_status and \
                      self.health_status[provider_name].is_healthy
        
        stats = adapter.get_stats()
        status = ProviderHealthStatus(
            provider_name=provider_name,
            is_healthy=is_healthy,
            is_degraded=adapter.is_degraded(),
            last_check=datetime.utcnow(),
            consecutive_failures=adapter.consecutive_failures,
            failure_rate=stats["failure_rate"],
            status_message=self._get_status_message(is_healthy, adapter),
        )
        
        self.health_status[provider_name] = status
        
        # Trigger callbacks on status change
        if not was_healthy and is_healthy:
            logger.info(f"Provider recovered: {provider_name}")
            if self.on_provider_recovered:
                try:
                    self.on_provider_recovered(provider_name)
                except Exception as e:
                    logger.error(f"Recovery callback error: {e}")
        
        elif was_healthy and not is_healthy:
            logger.warning(f"Provider failed: {provider_name}")
            if self.on_provider_failed:
                try:
                    self.on_provider_failed(provider_name)
                except Exception as e:
                    logger.error(f"Failure callback error: {e}")
        
        if adapter.is_degraded() and provider_name not in self.health_status:
            logger.warning(f"Provider degraded: {provider_name}")
            if self.on_provider_degraded:
                try:
                    self.on_provider_degraded(provider_name)
                except Exception as e:
                    logger.error(f"Degradation callback error: {e}")
    
    def _get_status_message(self, is_healthy: bool, adapter: BaseAdapter) -> str:
        """Get human-readable status message."""
        if is_healthy:
            return "Healthy"
        
        if adapter.is_degraded():
            return f"Degraded ({adapter.consecutive_failures} consecutive failures)"
        
        return f"Unhealthy (failure rate: {adapter.get_stats()['failure_rate']:.1%})"
    
    def get_health_status(
        self,
        provider_name: str = None
    ) -> Dict[str, ProviderHealthStatus] | ProviderHealthStatus:
        """
        Get health status for provider(s).
        
        Args:
            provider_name: Specific provider (None for all)
        
        Returns:
            Health status dict or single status
        """
        if provider_name:
            return self.health_status.get(provider_name)
        
        return self.health_status
    
    def is_provider_healthy(self, provider_name: str) -> bool:
        """Check if provider is healthy."""
        status = self.health_status.get(provider_name)
        return status.is_healthy if status else False
    
    def is_provider_degraded(self, provider_name: str) -> bool:
        """Check if provider is degraded."""
        status = self.health_status.get(provider_name)
        return status.is_degraded if status else False
    
    def get_healthy_providers(self) -> List[str]:
        """Get list of healthy provider names."""
        return [
            name for name, status in self.health_status.items()
            if status.is_healthy and not status.is_degraded
        ]
    
    def get_degraded_providers(self) -> List[str]:
        """Get list of degraded provider names."""
        return [
            name for name, status in self.health_status.items()
            if status.is_degraded
        ]
    
    def get_overall_health(self) -> Dict[str, any]:
        """Get overall system health."""
        if not self.health_status:
            return {
                "status": "unknown",
                "healthy_providers": 0,
                "degraded_providers": 0,
                "unhealthy_providers": 0,
                "avg_failure_rate": 0.0,
            }
        
        healthy = sum(1 for s in self.health_status.values() if s.is_healthy)
        degraded = sum(1 for s in self.health_status.values() if s.is_degraded)
        unhealthy = len(self.health_status) - healthy
        avg_failure = sum(s.failure_rate for s in self.health_status.values()) / len(self.health_status)
        
        # Determine overall status
        if unhealthy > len(self.health_status) / 2:
            status = "critical"
        elif degraded > 0:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "healthy_providers": healthy,
            "degraded_providers": degraded,
            "unhealthy_providers": unhealthy,
            "avg_failure_rate": avg_failure,
        }


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get or create global health monitor."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


# Fallback strategy functions

async def attempt_fallback(
    adapter: BaseAdapter,
    operation: str,
    parameters: Dict,
    correlation_id: str = None,
) -> Optional:
    """
    Attempt to execute operation with fallback if available.
    
    Args:
        adapter: Primary adapter
        operation: Operation name
        parameters: Operation parameters
        correlation_id: Trace correlation ID
    
    Returns:
        Result if successful (from primary or fallback), None on complete failure
    """
    # Try primary adapter
    response = await adapter.call(
        operation=operation,
        parameters=parameters,
        correlation_id=correlation_id,
    )
    
    if response.success:
        return response.data
    
    # If primary failed and has fallback, try fallback
    if adapter.fallback_adapter:
        logger.info(
            f"Primary adapter {adapter.provider_name} failed, trying fallback",
            extra={"correlation_id": correlation_id}
        )
        
        fallback_response = await adapter.fallback_adapter.call(
            operation=operation,
            parameters=parameters,
            correlation_id=correlation_id,
        )
        
        if fallback_response.success:
            return fallback_response.data
    
    return None
