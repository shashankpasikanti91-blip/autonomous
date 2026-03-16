"""
Platform observability and monitoring for multi-tenant SaaS system.

Provides metrics, logging, tracing, alerting, and platform health dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict

from saas_platform.models import generate_platform_id


logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Metric data point."""
    metric_id: str
    metric_name: str
    tenant_id: Optional[str] = None
    value: float = 0.0
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MetricWindow:
    """Window of metric aggregation."""
    metric_name: str
    tenant_id: Optional[str] = None
    period: str = "1m"  # 1m, 5m, 1h, 1d
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime = field(default_factory=datetime.utcnow)
    data_points: List[Metric] = field(default_factory=list)
    
    @property
    def avg_value(self) -> float:
        """Calculate average value."""
        if not self.data_points:
            return 0.0
        return sum(m.value for m in self.data_points) / len(self.data_points)
    
    @property
    def max_value(self) -> float:
        """Calculate max value."""
        if not self.data_points:
            return 0.0
        return max(m.value for m in self.data_points)
    
    @property
    def min_value(self) -> float:
        """Calculate min value."""
        if not self.data_points:
            return 0.0
        return min(m.value for m in self.data_points)


@dataclass
class ExecutionMetrics:
    """Metrics for workflow/app execution."""
    execution_id: str
    tenant_id: str
    app_id: str
    workflow_id: str
    status: str
    duration_ms: int
    memory_used_mb: int
    cpu_used_percent: float
    cost: float
    api_calls: int
    storage_read_gb: float
    storage_write_gb: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class TenantMetrics:
    """Aggregated metrics for tenant."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    executions_count: int = 0
    executions_failed: int = 0
    executions_success_rate: float = 100.0
    avg_execution_duration_ms: float = 0.0
    api_calls_total: int = 0
    storage_used_gb: float = 0.0
    total_cost: float = 0.0
    memory_peak_mb: int = 0
    cpu_peak_percent: float = 0.0
    uptime_percent: float = 99.9


@dataclass
class Alert:
    """System alert."""
    alert_id: str
    alert_type: str  # quota_exceeded, high_latency, error_rate, cost_spike
    severity: str = "warning"  # info, warning, critical
    tenant_id: Optional[str] = None
    title: str = ""
    description: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformHealthStatus:
    """Overall platform health status."""
    status: str = "healthy"  # healthy, degraded, critical
    uptime_percent: float = 100.0
    response_time_p99_ms: float = 0.0
    error_rate_percent: float = 0.0
    active_tenants: int = 0
    active_executions: int = 0
    worker_pool_utilization: float = 0.0
    database_connections_used: int = 0
    database_connections_total: int = 100
    cache_hit_rate: float = 95.0
    api_rate_limit_violations: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLog:
    """Audit trail entry."""
    log_id: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    changes: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"  # success, failure
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class MetricsCollector:
    """Collects metrics across platform."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: Dict[str, Metric] = {}
        self.metric_timeseries: Dict[str, List[Metric]] = defaultdict(list)
        self.windows: Dict[str, MetricWindow] = {}
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "",
        tenant_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Metric:
        """Record metric."""
        metric_id = generate_platform_id("metric")
        
        metric = Metric(
            metric_id=metric_id,
            metric_name=metric_name,
            value=value,
            unit=unit,
            tenant_id=tenant_id,
            tags=tags or {}
        )
        
        self.metrics[metric_id] = metric
        
        # Store in timeseries
        key = f"{metric_name}:{tenant_id or 'platform'}"
        self.metric_timeseries[key].append(metric)
        
        return metric
    
    def record_execution_metrics(
        self,
        execution_id: str,
        tenant_id: str,
        app_id: str,
        workflow_id: str,
        status: str,
        duration_ms: int,
        memory_mb: int,
        cpu_percent: float,
        cost: float,
        api_calls: int = 0,
        storage_read_gb: float = 0.0,
        storage_write_gb: float = 0.0
    ) -> ExecutionMetrics:
        """Record execution metrics."""
        metrics = ExecutionMetrics(
            execution_id=execution_id,
            tenant_id=tenant_id,
            app_id=app_id,
            workflow_id=workflow_id,
            status=status,
            duration_ms=duration_ms,
            memory_used_mb=memory_mb,
            cpu_used_percent=cpu_percent,
            cost=cost,
            api_calls=api_calls,
            storage_read_gb=storage_read_gb,
            storage_write_gb=storage_write_gb
        )
        
        # Record individual metrics
        self.record_metric(f"execution_duration_ms", duration_ms, "ms", tenant_id)
        self.record_metric(f"execution_memory_mb", memory_mb, "MB", tenant_id)
        self.record_metric(f"execution_cpu_percent", cpu_percent, "%", tenant_id)
        self.record_metric(f"execution_cost", cost, "$", tenant_id)
        
        if status == "success":
            self.record_metric(f"execution_success", 1, "", tenant_id)
        else:
            self.record_metric(f"execution_failure", 1, "", tenant_id)
        
        logger.info(f"Recorded execution metrics for {execution_id}")
        
        return metrics
    
    def get_metrics_range(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tenant_id: Optional[str] = None
    ) -> List[Metric]:
        """Get metrics for time range."""
        key = f"{metric_name}:{tenant_id or 'platform'}"
        timeseries = self.metric_timeseries.get(key, [])
        
        return [
            m for m in timeseries
            if start_time <= m.timestamp <= end_time
        ]
    
    def create_metric_window(
        self,
        metric_name: str,
        period: str = "1m",
        tenant_id: Optional[str] = None
    ) -> MetricWindow:
        """Create metric aggregation window."""
        now = datetime.utcnow()
        
        # Calculate period duration
        period_map = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "1h": timedelta(hours=1),
            "1d": timedelta(days=1)
        }
        
        duration = period_map.get(period, timedelta(minutes=1))
        start_time = now - duration
        
        # Get metrics for period
        data_points = self.get_metrics_range(
            metric_name,
            start_time,
            now,
            tenant_id
        )
        
        window = MetricWindow(
            metric_name=metric_name,
            tenant_id=tenant_id,
            period=period,
            start_time=start_time,
            end_time=now,
            data_points=data_points
        )
        
        return window


class ExecutionCostTracker:
    """Tracks execution costs."""
    
    def __init__(self):
        """Initialize cost tracker."""
        self.execution_costs: Dict[str, Dict[str, float]] = {}
        self.tenant_costs: Dict[str, Dict[str, float]] = defaultdict(lambda: {"total": 0.0})
    
    def calculate_execution_cost(
        self,
        duration_ms: int,
        memory_mb: int,
        cpu_percent: float
    ) -> float:
        """Calculate cost for execution."""
        # Pricing model
        duration_cost = (duration_ms / 1000.0) * 0.0001  # $0.0001 per second
        memory_cost = (memory_mb / 1024.0) * 0.0001  # $0.0001 per GB-second
        cpu_cost = (cpu_percent / 100.0) * 0.00005  # $0.00005 per % per second
        
        total_cost = duration_cost + memory_cost + cpu_cost
        return round(total_cost, 6)
    
    def record_execution_cost(
        self,
        execution_id: str,
        tenant_id: str,
        cost: float,
        breakdown: Optional[Dict[str, float]] = None
    ) -> None:
        """Record execution cost."""
        self.execution_costs[execution_id] = {
            "tenant_id": tenant_id,
            "cost": cost,
            "breakdown": breakdown or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.tenant_costs[tenant_id]["total"] += cost
    
    def get_tenant_monthly_cost(self, tenant_id: str) -> float:
        """Get monthly cost estimate for tenant."""
        return self.tenant_costs[tenant_id]["total"]
    
    def get_cost_breakdown(self, tenant_id: str) -> Dict[str, float]:
        """Get cost breakdown for tenant."""
        breakdown = defaultdict(float)
        
        for exec_id, cost_info in self.execution_costs.items():
            if cost_info["tenant_id"] == tenant_id:
                for category, amount in cost_info.get("breakdown", {}).items():
                    breakdown[category] += amount
        
        return dict(breakdown)


class SLAMonitor:
    """Monitors SLA compliance."""
    
    def __init__(self):
        """Initialize SLA monitor."""
        self.sla_targets = {
            "availability": 99.9,  # percent
            "response_time_p99": 1000,  # milliseconds
            "error_rate": 0.1  # percent
        }
        self.current_metrics: Dict[str, float] = {}
        self.sla_breaches: List[Dict[str, Any]] = []
    
    def check_sla_compliance(
        self,
        availability: float,
        response_time_p99: float,
        error_rate: float
    ) -> Dict[str, bool]:
        """Check SLA compliance."""
        compliance = {
            "availability": availability >= self.sla_targets["availability"],
            "response_time": response_time_p99 <= self.sla_targets["response_time_p99"],
            "error_rate": error_rate <= self.sla_targets["error_rate"]
        }
        
        overall_compliant = all(compliance.values())
        
        if not overall_compliant:
            breach = {
                "timestamp": datetime.utcnow().isoformat(),
                "availability": availability,
                "response_time_p99": response_time_p99,
                "error_rate": error_rate,
                "compliance": compliance
            }
            self.sla_breaches.append(breach)
            logger.warning(f"SLA breach detected: {compliance}")
        
        return compliance
    
    def get_sla_status(self) -> Dict[str, Any]:
        """Get SLA status."""
        compliant_periods = len(
            [b for b in self.sla_breaches if all(b["compliance"].values())]
        )
        
        return {
            "targets": self.sla_targets,
            "current_metrics": self.current_metrics,
            "total_breaches": len(self.sla_breaches),
            "compliance_rate": (
                (len(self.sla_breaches) - compliant_periods) / len(self.sla_breaches)
                if self.sla_breaches else 100.0
            )
        }


class PlatformHealthDashboard:
    """Platform health dashboard."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        cost_tracker: ExecutionCostTracker,
        sla_monitor: SLAMonitor
    ):
        """Initialize health dashboard."""
        self.metrics_collector = metrics_collector
        self.cost_tracker = cost_tracker
        self.sla_monitor = sla_monitor
    
    def get_platform_health(self) -> PlatformHealthStatus:
        """Get platform health status."""
        # Get metrics windows
        response_time_window = self.metrics_collector.create_metric_window(
            "response_time_ms",
            "5m"
        )
        error_rate_window = self.metrics_collector.create_metric_window(
            "error_rate_percent",
            "5m"
        )
        
        # Calculate P99
        response_times = sorted([m.value for m in response_time_window.data_points])
        response_time_p99 = (
            response_times[int(len(response_times) * 0.99)]
            if response_times else 0.0
        )
        
        # Check SLA
        self.sla_monitor.check_sla_compliance(
            availability=99.95,
            response_time_p99=response_time_p99,
            error_rate=error_rate_window.avg_value
        )
        
        status = "healthy"
        if error_rate_window.avg_value > 1.0 or response_time_p99 > 5000:
            status = "degraded"
        if error_rate_window.avg_value > 5.0:
            status = "critical"
        
        return PlatformHealthStatus(
            status=status,
            response_time_p99_ms=response_time_p99,
            error_rate_percent=error_rate_window.avg_value,
            uptime_percent=99.95
        )
    
    def get_tenant_health(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant health metrics."""
        metrics = self.metrics_collector.create_metric_window(
            f"execution_duration_ms",
            "1h",
            tenant_id
        )
        
        return {
            "tenant_id": tenant_id,
            "executions_count": len(metrics.data_points),
            "avg_duration_ms": metrics.avg_value,
            "max_duration_ms": metrics.max_value,
            "monthly_cost": self.cost_tracker.get_tenant_monthly_cost(tenant_id)
        }


class AlertManager:
    """Manages system alerts."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[callable] = []
    
    def create_alert(
        self,
        alert_type: str,
        title: str,
        description: str,
        severity: str = "warning",
        tenant_id: Optional[str] = None,
        metric_value: float = 0.0,
        threshold: float = 0.0
    ) -> Alert:
        """Create alert."""
        alert_id = generate_platform_id("alert")
        
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            title=title,
            description=description,
            severity=severity,
            tenant_id=tenant_id,
            metric_value=metric_value,
            threshold=threshold
        )
        
        self.alerts[alert_id] = alert
        
        # Trigger handlers
        for handler in self.alert_handlers:
            handler(alert)
        
        level = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "critical": logging.CRITICAL
        }.get(severity, logging.WARNING)
        
        logger.log(
            level,
            f"[{severity.upper()}] {title}: {description}"
        )
        
        return alert
    
    def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str
    ) -> bool:
        """Acknowledge alert."""
        alert = self.alerts.get(alert_id)
        if not alert:
            logger.error(f"Alert not found: {alert_id}")
            return False
        
        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        
        logger.info(f"Alert acknowledged: {alert_id} by {user_id}")
        return True
    
    def register_alert_handler(self, handler: callable) -> None:
        """Register alert handler."""
        self.alert_handlers.append(handler)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [a for a in self.alerts.values() if not a.acknowledged]


class AuditLogger:
    """Logs audit trail for compliance."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.logs: Dict[str, AuditLog] = {}
        self.tenant_logs: Dict[str, List[str]] = defaultdict(list)
    
    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str = "",
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> AuditLog:
        """Log audit action."""
        log_id = generate_platform_id("audit")
        
        log = AuditLog(
            log_id=log_id,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes or {},
            status=status
        )
        
        self.logs[log_id] = log
        
        if tenant_id:
            self.tenant_logs[tenant_id].append(log_id)
        
        return log
    
    def get_tenant_audit_logs(
        self,
        tenant_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for tenant."""
        log_ids = self.tenant_logs.get(tenant_id, [])
        
        logs = [
            self.logs[lid]
            for lid in log_ids[-limit:]
            if lid in self.logs
        ]
        
        return list(reversed(logs))
