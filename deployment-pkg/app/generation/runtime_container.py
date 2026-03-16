"""
App runtime container - isolates generated apps with resource constraints.

Manages app instances, quotas, execution, and monitoring.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Coroutine
from enum import Enum

from .models import (
    AppInstance, ResourceQuota, AppExecutionLog, AppAnalytics,
    AppEvolutionSuggestion, AppPackage, generate_id
)


class AppInstanceStatus(str, Enum):
    """Status of app instance."""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


@dataclass
class ResourceUsage:
    """Current resource usage."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    requests_current_hour: int = 0
    storage_mb: float = 0.0
    concurrent_connections: int = 0


@dataclass
class QuotaViolation:
    """Record of quota violation."""
    violation_id: str
    instance_id: str
    quota_type: str  # memory, requests, storage, connections
    limit: int
    actual: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ResourceMonitor:
    """Monitors resource usage of app instances."""
    
    def __init__(self):
        self.usage_history: Dict[str, List[ResourceUsage]] = {}
        self.violations: Dict[str, List[QuotaViolation]] = {}
    
    def record_usage(self, instance_id: str, usage: ResourceUsage) -> None:
        """Record resource usage."""
        if instance_id not in self.usage_history:
            self.usage_history[instance_id] = []
        self.usage_history[instance_id].append(usage)
    
    def check_quota_violation(
        self,
        instance_id: str,
        usage: ResourceUsage,
        quota: ResourceQuota
    ) -> Optional[QuotaViolation]:
        """Check if quota is violated."""
        
        if usage.memory_mb > quota.max_memory_mb:
            violation = QuotaViolation(
                violation_id=generate_id("violation"),
                instance_id=instance_id,
                quota_type="memory",
                limit=quota.max_memory_mb,
                actual=int(usage.memory_mb)
            )
            if instance_id not in self.violations:
                self.violations[instance_id] = []
            self.violations[instance_id].append(violation)
            return violation
        
        if usage.requests_current_hour > quota.max_requests_per_hour:
            violation = QuotaViolation(
                violation_id=generate_id("violation"),
                instance_id=instance_id,
                quota_type="requests",
                limit=quota.max_requests_per_hour,
                actual=usage.requests_current_hour
            )
            if instance_id not in self.violations:
                self.violations[instance_id] = []
            self.violations[instance_id].append(violation)
            return violation
        
        if usage.storage_mb > quota.max_storage_gb * 1024:
            violation = QuotaViolation(
                violation_id=generate_id("violation"),
                instance_id=instance_id,
                quota_type="storage",
                limit=int(quota.max_storage_gb * 1024),
                actual=int(usage.storage_mb)
            )
            if instance_id not in self.violations:
                self.violations[instance_id] = []
            self.violations[instance_id].append(violation)
            return violation
        
        if usage.concurrent_connections > quota.max_concurrent_connections:
            violation = QuotaViolation(
                violation_id=generate_id("violation"),
                instance_id=instance_id,
                quota_type="connections",
                limit=quota.max_concurrent_connections,
                actual=usage.concurrent_connections
            )
            if instance_id not in self.violations:
                self.violations[instance_id] = []
            self.violations[instance_id].append(violation)
            return violation
        
        return None
    
    def get_usage_statistics(
        self,
        instance_id: str,
        period_hours: int = 1
    ) -> Dict[str, Any]:
        """Get usage statistics for period."""
        if instance_id not in self.usage_history:
            return {}
        
        usage_list = self.usage_history[instance_id]
        if not usage_list:
            return {}
        
        recent_usage = usage_list[-1]  # Get last recorded usage
        
        return {
            "cpu_percent": recent_usage.cpu_percent,
            "memory_mb": recent_usage.memory_mb,
            "requests_current_hour": recent_usage.requests_current_hour,
            "storage_mb": recent_usage.storage_mb,
            "concurrent_connections": recent_usage.concurrent_connections
        }


class ExecutionEnvironment:
    """Isolated execution environment for app."""
    
    def __init__(self, instance: AppInstance):
        self.instance = instance
        self.execution_logs: List[AppExecutionLog] = []
        self.monitor = ResourceMonitor()
    
    async def execute_operation(
        self,
        operation_name: str,
        handler: Callable[[], Coroutine]
    ) -> tuple[bool, Any, Optional[str]]:
        """Execute operation within environment."""
        log_id = generate_id("log")
        start_time = datetime.utcnow()
        
        try:
            # Check quota before execution
            usage = ResourceUsage(
                requests_current_hour=len(self.execution_logs)
            )
            violation = self.monitor.check_quota_violation(
                self.instance.instance_id,
                usage,
                self.instance.quota
            )
            
            if violation:
                log = AppExecutionLog(
                    log_id=log_id,
                    instance_id=self.instance.instance_id,
                    operation=operation_name,
                    status="blocked",
                    error=f"Quota violation: {violation.quota_type}"
                )
                self.execution_logs.append(log)
                return False, None, f"Quota violation: {violation.quota_type}"
            
            # Execute operation
            result = await handler()
            
            # Record success
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            log = AppExecutionLog(
                log_id=log_id,
                instance_id=self.instance.instance_id,
                operation=operation_name,
                status="success",
                duration_ms=duration
            )
            self.execution_logs.append(log)
            
            # Record usage
            usage.requests_current_hour = len(self.execution_logs)
            self.monitor.record_usage(self.instance.instance_id, usage)
            
            return True, result, None
            
        except Exception as e:
            # Record failure
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            log = AppExecutionLog(
                log_id=log_id,
                instance_id=self.instance.instance_id,
                operation=operation_name,
                status="error",
                duration_ms=duration,
                error=str(e)
            )
            self.execution_logs.append(log)
            
            return False, None, str(e)


class AppRuntimeContainer:
    """Runtime container for generated apps."""
    
    def __init__(self):
        self.instances: Dict[str, AppInstance] = {}
        self.environments: Dict[str, ExecutionEnvironment] = {}
        self.analytics: Dict[str, AppAnalytics] = {}
        self.suggestions: Dict[str, List[AppEvolutionSuggestion]] = {}
    
    async def create_instance(
        self,
        package: AppPackage,
        environment_variables: Optional[Dict[str, str]] = None,
        quota: Optional[ResourceQuota] = None
    ) -> AppInstance:
        """Create app instance from package."""
        
        if quota is None:
            quota = ResourceQuota(quota_id=generate_id("quota"))
        
        instance = AppInstance(
            instance_id=generate_id("instance"),
            package_id=package.package_id,
            app_name=package.app_name,
            version=package.version,
            status="created",
            quota=quota,
            environment_variables=environment_variables or {}
        )
        
        self.instances[instance.instance_id] = instance
        self.environments[instance.instance_id] = ExecutionEnvironment(instance)
        
        return instance
    
    async def start_instance(self, instance_id: str) -> tuple[bool, Optional[str]]:
        """Start app instance."""
        if instance_id not in self.instances:
            return False, "Instance not found"
        
        instance = self.instances[instance_id]
        
        try:
            instance.status = "initializing"
            
            # Simulate initialization
            await asyncio.sleep(0.1)
            
            instance.status = "running"
            instance.started_at = datetime.utcnow()
            
            return True, None
        except Exception as e:
            instance.status = "error"
            return False, str(e)
    
    async def stop_instance(self, instance_id: str) -> tuple[bool, Optional[str]]:
        """Stop app instance."""
        if instance_id not in self.instances:
            return False, "Instance not found"
        
        instance = self.instances[instance_id]
        
        try:
            instance.status = "stopping"
            
            # Simulate shutdown
            await asyncio.sleep(0.1)
            
            instance.status = "stopped"
            instance.stopped_at = datetime.utcnow()
            
            return True, None
        except Exception as e:
            instance.status = "error"
            return False, str(e)
    
    async def pause_instance(self, instance_id: str) -> tuple[bool, Optional[str]]:
        """Pause app instance."""
        if instance_id not in self.instances:
            return False, "Instance not found"
        
        instance = self.instances[instance_id]
        instance.status = "paused"
        return True, None
    
    async def resume_instance(self, instance_id: str) -> tuple[bool, Optional[str]]:
        """Resume paused app instance."""
        if instance_id not in self.instances:
            return False, "Instance not found"
        
        instance = self.instances[instance_id]
        if instance.status == "paused":
            instance.status = "running"
        return True, None
    
    async def execute_in_instance(
        self,
        instance_id: str,
        operation_name: str,
        handler: Callable[[], Coroutine]
    ) -> tuple[bool, Any, Optional[str]]:
        """Execute operation in instance environment."""
        if instance_id not in self.environments:
            return False, None, "Instance not found"
        
        if instance_id in self.instances:
            instance = self.instances[instance_id]
            if instance.status != "running":
                return False, None, f"Instance is {instance.status}"
        
        environment = self.environments[instance_id]
        return await environment.execute_operation(operation_name, handler)
    
    def collect_analytics(
        self,
        instance_id: str,
        period_hours: int = 1
    ) -> AppAnalytics:
        """Collect analytics for instance."""
        if instance_id not in self.environments:
            return None
        
        environment = self.environments[instance_id]
        logs = environment.execution_logs
        
        # Filter logs to period
        cutoff_time = datetime.utcnow() - timedelta(hours=period_hours)
        period_logs = [l for l in logs if l.timestamp >= cutoff_time]
        
        total = len(period_logs)
        successful = len([l for l in period_logs if l.status == "success"])
        failed = len([l for l in period_logs if l.status == "error"])
        blocked = len([l for l in period_logs if l.status == "blocked"])
        
        # Calculate response times
        response_times = [l.duration_ms for l in period_logs if l.duration_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # P95 and P99 percentiles
        sorted_times = sorted(response_times)
        p95_idx = int(len(sorted_times) * 0.95) if sorted_times else 0
        p99_idx = int(len(sorted_times) * 0.99) if sorted_times else 0
        p95 = sorted_times[p95_idx] if p95_idx < len(sorted_times) else 0.0
        p99 = sorted_times[p99_idx] if p99_idx < len(sorted_times) else 0.0
        
        # Count errors by type
        errors_by_type = {}
        for log in period_logs:
            if log.error:
                error_type = log.error.split(":")[0]
                errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
        
        analytics = AppAnalytics(
            analytics_id=generate_id("analytics"),
            instance_id=instance_id,
            period_start=cutoff_time,
            period_end=datetime.utcnow(),
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            errors_by_type=errors_by_type
        )
        
        return analytics
    
    def generate_evolution_suggestions(
        self,
        instance_id: str
    ) -> List[AppEvolutionSuggestion]:
        """Generate suggestions for app evolution."""
        
        if instance_id not in self.instances:
            return []
        
        suggestions = []
        
        # Collect analytics
        analytics = self.collect_analytics(instance_id)
        if not analytics:
            return []
        
        # Check error rate
        if analytics.total_requests > 0:
            error_rate = (analytics.failed_requests + len(analytics.errors_by_type)) / analytics.total_requests
            if error_rate > 0.05:  # > 5% error rate
                suggestions.append(AppEvolutionSuggestion(
                    suggestion_id=generate_id("suggestion"),
                    instance_id=instance_id,
                    category="reliability",
                    priority="high",
                    description=f"High error rate ({error_rate*100:.1f}%) detected. Review error logs and add error handling.",
                    implementation_effort="medium",
                    estimated_impact="high"
                ))
        
        # Check performance
        if analytics.avg_response_time_ms > 500:
            suggestions.append(AppEvolutionSuggestion(
                suggestion_id=generate_id("suggestion"),
                instance_id=instance_id,
                category="performance",
                priority="medium",
                description=f"Slow response times ({analytics.avg_response_time_ms:.0f}ms). Consider adding caching or optimization.",
                implementation_effort="medium",
                estimated_impact="medium"
            ))
        
        # Check P95 spike
        if analytics.p95_response_time_ms > analytics.avg_response_time_ms * 5:
            suggestions.append(AppEvolutionSuggestion(
                suggestion_id=generate_id("suggestion"),
                instance_id=instance_id,
                category="performance",
                priority="medium",
                description="High P95 response time indicates occasional slowdowns. Profile and optimize hotspots.",
                implementation_effort="high",
                estimated_impact="medium"
            ))
        
        # Store suggestions
        if instance_id not in self.suggestions:
            self.suggestions[instance_id] = []
        self.suggestions[instance_id].extend(suggestions)
        
        return suggestions
    
    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get complete instance status."""
        if instance_id not in self.instances:
            return None
        
        instance = self.instances[instance_id]
        
        # Get environment stats
        environment = self.environments.get(instance_id)
        usage_stats = {}
        if environment:
            usage_stats = environment.monitor.get_usage_statistics(instance_id)
        
        # Get analytics
        analytics = self.collect_analytics(instance_id)
        
        status = {
            "instance_id": instance.instance_id,
            "app_name": instance.app_name,
            "version": instance.version,
            "status": instance.status,
            "created_at": instance.created_at.isoformat(),
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "uptime_seconds": (datetime.utcnow() - instance.started_at).total_seconds() if instance.started_at else 0,
            "resource_usage": usage_stats,
            "quota": {
                "max_requests_per_hour": instance.quota.max_requests_per_hour,
                "max_memory_mb": instance.quota.max_memory_mb,
                "max_storage_gb": instance.quota.max_storage_gb
            },
            "analytics": {
                "total_requests": analytics.total_requests if analytics else 0,
                "successful_requests": analytics.successful_requests if analytics else 0,
                "failed_requests": analytics.failed_requests if analytics else 0,
                "avg_response_time_ms": analytics.avg_response_time_ms if analytics else 0
            }
        }
        
        return status
