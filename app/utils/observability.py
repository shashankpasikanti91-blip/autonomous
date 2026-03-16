"""
Observability Layer

Provides:
- Structured logging
- Execution tracing
- Error tracking
- Performance metrics
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import time
import json

from utils.logger import get_logger


logger = get_logger(__name__)


class ExecutionTrace:
    """Represents a single execution trace."""
    
    def __init__(
        self,
        trace_id: str,
        service: str,
        operation: str,
        user_id: Optional[str] = None
    ):
        self.trace_id = trace_id
        self.service = service
        self.operation = operation
        self.user_id = user_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "running"
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.events: list = []
    
    def add_event(self, event_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the trace."""
        self.events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_name,
            "details": details or {}
        })
    
    def set_error(self, error: str) -> None:
        """Mark trace as failed with error message."""
        self.status = "failed"
        self.error = error
    
    def complete(self) -> None:
        """Mark trace as completed."""
        self.end_time = time.time()
        if self.status == "running":
            self.status = "completed"
    
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        if not self.end_time:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize trace to dictionary."""
        return {
            "trace_id": self.trace_id,
            "service": self.service,
            "operation": self.operation,
            "user_id": self.user_id,
            "status": self.status,
            "duration_ms": self.duration_ms(),
            "error": self.error,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "events": self.events,
            "metadata": self.metadata
        }


class MetricsCollector:
    """Collects and aggregates performance metrics."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.MetricsCollector")
        self.metrics: Dict[str, list] = {}
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Numeric value
            tags: Optional tags for categorization
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "timestamp": datetime.utcnow().isoformat(),
            "value": value,
            "tags": tags or {}
        })
    
    def get_metric_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for a metric."""
        if metric_name not in self.metrics:
            return None
        
        values = [m["value"] for m in self.metrics[metric_name]]
        
        if not values:
            return None
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values)
        }
    
    def clear_metric(self, metric_name: str, older_than_hours: int = 24) -> int:
        """
        Clear old metric entries.
        
        Args:
            metric_name: Metric to clear
            older_than_hours: Remove entries older than this many hours
            
        Returns:
            Number of entries removed
        """
        if metric_name not in self.metrics:
            return 0
        
        cutoff_time = (
            datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            - timedelta(hours=older_than_hours)
        ).isoformat()
        
        original_count = len(self.metrics[metric_name])
        self.metrics[metric_name] = [
            m for m in self.metrics[metric_name]
            if m["timestamp"] > cutoff_time
        ]
        
        return original_count - len(self.metrics[metric_name])


class ErrorTracker:
    """Tracks and aggregates errors."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.ErrorTracker")
        self.errors: list = []
        self.error_counts: Dict[str, int] = {}
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error"
    ) -> None:
        """
        Record an error.
        
        Args:
            error_type: Type of error (e.g., "ValueError")
            error_message: Error message text
            context: Additional context
            severity: Severity level (debug, info, warning, error, critical)
        """
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": error_message,
            "severity": severity,
            "context": context or {}
        }
        
        self.errors.append(error_record)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        self.logger.warning(
            f"Error recorded: {error_type} - {error_message}",
            extra={"error_record": error_record}
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recorded errors."""
        return {
            "total_errors": len(self.errors),
            "unique_types": len(self.error_counts),
            "error_counts": self.error_counts,
            "most_common": max(
                self.error_counts.items(),
                key=lambda x: x[1],
                default=(None, 0)
            )[0]
        }
    
    def clear_errors(self, older_than_hours: int = 24) -> int:
        """Clear old error records."""
        from datetime import timedelta
        
        cutoff_time = (
            datetime.utcnow() - timedelta(hours=older_than_hours)
        )
        
        original_count = len(self.errors)
        self.errors = [
            e for e in self.errors
            if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]
        
        return original_count - len(self.errors)


class Observability:
    """Central observability coordinator."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.Observability")
        self.metrics = MetricsCollector()
        self.errors = ErrorTracker()
        self.traces: Dict[str, ExecutionTrace] = {}
    
    def start_trace(
        self,
        service: str,
        operation: str,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> ExecutionTrace:
        """Start a new execution trace."""
        if not trace_id:
            import uuid
            trace_id = str(uuid.uuid4())
        
        trace = ExecutionTrace(trace_id, service, operation, user_id)
        self.traces[trace_id] = trace
        
        self.logger.debug(f"Started trace: {trace_id} ({service}.{operation})")
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """Retrieve a trace."""
        return self.traces.get(trace_id)
    
    async def record_trace(self, trace: ExecutionTrace) -> None:
        """Record completed trace."""
        trace.complete()
        
        # Log trace
        self.logger.info(
            f"Trace completed: {trace.operation}",
            extra={
                "trace_id": trace.trace_id,
                "duration_ms": trace.duration_ms(),
                "status": trace.status,
                "error": trace.error
            }
        )
        
        # Record metric
        self.metrics.record_metric(
            f"{trace.service}.{trace.operation}.duration_ms",
            trace.duration_ms(),
            tags={"status": trace.status}
        )
        
        # Record error if failed
        if trace.status == "failed" and trace.error:
            self.errors.record_error(
                error_type=trace.operation,
                error_message=trace.error,
                context={"trace_id": trace.trace_id},
                severity="error"
            )
        
        # Keep in history
        self.traces[trace.trace_id] = trace
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        error_summary = self.errors.get_error_summary()
        
        return {
            "status": "healthy" if error_summary["total_errors"] == 0 else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "errors": error_summary,
            "recent_traces": len(self.traces),
            "metrics_recorded": len(self.metrics.metrics)
        }


# Singleton instances
_observability: Optional[Observability] = None


def get_observability() -> Observability:
    """Get or create observability singleton."""
    global _observability
    if _observability is None:
        _observability = Observability()
    return _observability


@asynccontextmanager
async def trace_operation(
    service: str,
    operation: str,
    user_id: Optional[str] = None
):
    """
    Context manager for tracing operations.
    
    Usage:
        async with trace_operation("email_service", "send_email") as trace:
            # Do work
            trace.add_event("email_sent", {"recipient": "user@example.com"})
    """
    obs = get_observability()
    trace = obs.start_trace(service, operation, user_id)
    
    try:
        yield trace
    
    except Exception as e:
        trace.set_error(str(e))
        raise
    
    finally:
        await obs.record_trace(trace)
