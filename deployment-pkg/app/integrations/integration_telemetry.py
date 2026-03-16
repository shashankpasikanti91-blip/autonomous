"""
Integration event telemetry for provider operations.
Tracks success/failure counters, latency metrics, and provider reliability scoring.
"""
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for provider operations."""
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    FALLBACK = "fallback"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    DEGRADATION = "degradation"
    RECOVERY = "recovery"


@dataclass
class ProviderEvent:
    """Single provider event for telemetry."""
    provider: str
    event_type: EventType
    operation: str
    
    latency_ms: float = 0.0              # Operation latency
    status_code: Optional[int] = None    # HTTP status if applicable
    error_message: Optional[str] = None  # Error message if failure
    retry_count: int = 0                 # Number of retries
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event."""
        return {
            "provider": self.provider,
            "event_type": self.event_type.value,
            "operation": self.operation,
            "latency_ms": self.latency_ms,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


@dataclass
class ProviderMetrics:
    """Aggregated metrics for a provider."""
    provider: str
    total_events: int = 0
    success_count: int = 0
    failure_count: int = 0
    retry_count: int = 0
    fallback_count: int = 0
    rate_limit_count: int = 0
    timeout_count: int = 0
    
    success_rate: float = 0.0              # 0.0 to 1.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    operation_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)
    last_failure_time: Optional[datetime] = None
    time_since_failure_seconds: Optional[int] = None
    
    uptime_percentage: float = 0.0        # Last 24 hours
    reliability_score: float = 1.0        # 0.0 to 1.0 (1.0 = perfect)


class IntegrationTelemetry:
    """
    Tracks integration provider events and metrics.
    
    Provides:
    - Event recording (success, failure, retry, etc)
    - Metric aggregation
    - Provider reliability scoring
    - Event querying and history
    """
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize telemetry.
        
        Args:
            retention_hours: How long to retain events (default 24 hours)
        """
        self.retention_hours = retention_hours
        self.events: List[ProviderEvent] = []
        self.metrics: Dict[str, ProviderMetrics] = {}
        self.operation_latencies: Dict[str, List[float]] = {}  # {provider.operation: [latencies]}
    
    def record_event(self, event: ProviderEvent):
        """Record provider event."""
        # Store event
        self.events.append(event)
        
        # Update metrics
        self._update_metrics(event)
        
        # Store latency samples
        op_key = f"{event.provider}.{event.operation}"
        if op_key not in self.operation_latencies:
            self.operation_latencies[op_key] = []
        self.operation_latencies[op_key].append(event.latency_ms)
        
        # Cleanup old latency samples (keep last 1000)
        if len(self.operation_latencies[op_key]) > 1000:
            self.operation_latencies[op_key] = self.operation_latencies[op_key][-1000:]
        
        logger.debug(f"Telemetry event recorded: {event.provider}.{event.operation}")
    
    def _update_metrics(self, event: ProviderEvent):
        """Update aggregated metrics from event."""
        provider = event.provider
        
        # Initialize metrics if needed
        if provider not in self.metrics:
            self.metrics[provider] = ProviderMetrics(provider=provider)
        
        metrics = self.metrics[provider]
        
        # Update counters
        metrics.total_events += 1
        
        match event.event_type:
            case EventType.SUCCESS:
                metrics.success_count += 1
            case EventType.FAILURE:
                metrics.failure_count += 1
                metrics.last_failure_time = event.timestamp
            case EventType.RETRY:
                metrics.retry_count += 1
            case EventType.FALLBACK:
                metrics.fallback_count += 1
            case EventType.RATE_LIMIT:
                metrics.rate_limit_count += 1
            case EventType.TIMEOUT:
                metrics.timeout_count += 1
        
        # Update operation breakdown
        op = event.operation
        if op not in metrics.operation_breakdown:
            metrics.operation_breakdown[op] = {
                "success": 0,
                "failure": 0,
                "total": 0,
            }
        
        metrics.operation_breakdown[op]["total"] += 1
        if event.event_type == EventType.SUCCESS:
            metrics.operation_breakdown[op]["success"] += 1
        elif event.event_type == EventType.FAILURE:
            metrics.operation_breakdown[op]["failure"] += 1
        
        # Update aggregates
        self._recalculate_aggregates(provider)
    
    def _recalculate_aggregates(self, provider: str):
        """Recalculate aggregated metrics."""
        metrics = self.metrics[provider]
        
        # Success rate
        if metrics.total_events > 0:
            metrics.success_rate = metrics.success_count / metrics.total_events
        
        # Latency percentiles
        op_key = f"{provider}.*"  # All operations for this provider
        all_latencies = []
        for key, latencies in self.operation_latencies.items():
            if key.startswith(provider):
                all_latencies.extend(latencies)
        
        if all_latencies:
            metrics.avg_latency_ms = statistics.mean(all_latencies)
            if len(all_latencies) >= 20:
                all_latencies_sorted = sorted(all_latencies)
                metrics.p95_latency_ms = all_latencies_sorted[int(len(all_latencies) * 0.95)]
                metrics.p99_latency_ms = all_latencies_sorted[int(len(all_latencies) * 0.99)]
        
        # Time since last failure
        if metrics.last_failure_time:
            time_diff = (datetime.utcnow() - metrics.last_failure_time).total_seconds()
            metrics.time_since_failure_seconds = int(time_diff)
        
        # Reliability score (0.0 to 1.0)
        # Based on: success rate (70%), time since failure (20%), latency (10%)
        success_component = metrics.success_rate * 0.7
        
        time_component = 0.0
        if metrics.time_since_failure_seconds:
            # Max credit after 1 hour without failure
            time_component = min(1.0, metrics.time_since_failure_seconds / 3600.0) * 0.2
        else:
            time_component = 0.2
        
        latency_component = 0.1
        if metrics.avg_latency_ms > 0:
            # Penalize high latency (> 5s = 0 points)
            latency_component = min(0.1, (1.0 - min(1.0, metrics.avg_latency_ms / 5000.0)) * 0.1)
        
        metrics.reliability_score = success_component + time_component + latency_component
        metrics.reliability_score = max(0.0, min(1.0, metrics.reliability_score))
    
    def get_metrics(self, provider: str = None) -> Dict[str, ProviderMetrics] | ProviderMetrics:
        """Get metrics for provider(s)."""
        if provider:
            return self.metrics.get(provider)
        return self.metrics
    
    def get_provider_events(
        self,
        provider: str,
        event_type: EventType = None,
        operation: str = None,
        limit: int = 100,
    ) -> List[ProviderEvent]:
        """
        Query provider events.
        
        Args:
            provider: Provider name
            event_type: Filter by event type (None for all)
            operation: Filter by operation (None for all)
            limit: Maximum events to return
        
        Returns:
            List of events matching criteria
        """
        results = [
            e for e in self.events
            if e.provider == provider
            and (event_type is None or e.event_type == event_type)
            and (operation is None or e.operation == operation)
        ]
        
        # Return most recent first
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_operation_stats(
        self,
        provider: str,
        operation: str,
    ) -> Dict[str, Any]:
        """Get statistics for specific operation."""
        op_key = f"{provider}.{operation}"
        
        if op_key not in self.operation_latencies:
            return {"samples": 0}
        
        latencies = self.operation_latencies[op_key]
        
        return {
            "samples": len(latencies),
            "avg_ms": statistics.mean(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "median_ms": statistics.median(latencies),
            "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        }
    
    def get_reliability_ranking(self) -> List[tuple[str, float]]:
        """Get providers ranked by reliability score."""
        scores = [
            (provider, metrics.reliability_score)
            for provider, metrics in self.metrics.items()
        ]
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def cleanup_old_events(self):
        """Remove events older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        before = len(self.events)
        self.events = [e for e in self.events if e.timestamp > cutoff_time]
        removed = before - len(self.events)
        if removed > 0:
            logger.debug(f"Cleaned up {removed} old telemetry events")
    
    def reset_provider(self, provider: str):
        """Reset metrics for provider."""
        self.metrics.pop(provider, None)
        self.events = [e for e in self.events if e.provider != provider]
        to_remove = [k for k in self.operation_latencies.keys() if k.startswith(provider)]
        for k in to_remove:
            del self.operation_latencies[k]
        logger.info(f"Reset telemetry for provider: {provider}")


# Global telemetry instance
_telemetry: Optional[IntegrationTelemetry] = None


def get_integration_telemetry() -> IntegrationTelemetry:
    """Get or create global integration telemetry."""
    global _telemetry
    if _telemetry is None:
        _telemetry = IntegrationTelemetry()
    return _telemetry


def record_provider_success(
    provider: str,
    operation: str,
    latency_ms: float,
    correlation_id: str = None,
    metadata: Dict[str, Any] = None,
):
    """Record successful provider operation."""
    telemetry = get_integration_telemetry()
    event = ProviderEvent(
        provider=provider,
        event_type=EventType.SUCCESS,
        operation=operation,
        latency_ms=latency_ms,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )
    telemetry.record_event(event)


def record_provider_failure(
    provider: str,
    operation: str,
    error_message: str,
    status_code: int = None,
    latency_ms: float = 0.0,
    correlation_id: str = None,
    metadata: Dict[str, Any] = None,
):
    """Record failed provider operation."""
    telemetry = get_integration_telemetry()
    event = ProviderEvent(
        provider=provider,
        event_type=EventType.FAILURE,
        operation=operation,
        error_message=error_message,
        status_code=status_code,
        latency_ms=latency_ms,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )
    telemetry.record_event(event)
