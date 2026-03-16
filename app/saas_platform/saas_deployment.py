"""
SaaS deployment architecture for stateless, scalable multi-tenant platform.

Provides API design, orchestration, worker management, and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Coroutine
import logging
from enum import Enum

from saas_platform.models import TenantContext, generate_platform_id


logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class WorkerType(str, Enum):
    """Background worker type."""
    BILLING = "billing"
    ANALYTICS = "analytics"
    CLEANUP = "cleanup"
    WEBHOOKS = "webhooks"
    NOTIFICATIONS = "notifications"


@dataclass
class EnvironmentConfig:
    """Configuration per environment."""
    environment: Environment
    api_endpoint: str
    database_url: str
    cache_url: str
    log_level: str = "INFO"
    max_request_timeout_seconds: int = 30
    request_batch_size: int = 100
    enable_profiling: bool = False
    enable_debug: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantEnvironmentConfig:
    """Per-tenant environment configuration."""
    tenant_id: str
    config_id: str = field(default_factory=lambda: generate_platform_id("tconfig"))
    webhook_url: Optional[str] = None
    custom_domain: Optional[str] = None
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    data_retention_days: int = 90
    backup_frequency: str = "daily"  # daily, weekly, monthly
    timezone: str = "UTC"
    locale: str = "en_US"
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RequestEnvelope:
    """Envelope for API requests."""
    request_id: str
    tenant_id: str
    user_id: Optional[str] = None
    api_key_prefix: Optional[str] = None
    endpoint: str = ""
    method: str = "POST"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseEnvelope:
    """Envelope for API responses."""
    request_id: str
    tenant_id: str
    status: str = "success"  # success, error
    status_code: int = 200
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BackgroundJob:
    """Background job for async processing."""
    job_id: str
    tenant_id: str
    job_type: str
    priority: int = 5  # 1-10, higher = more important
    status: str = "queued"  # queued, running, completed, failed
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedResource:
    """Shared resource pool for efficient multi-tenant execution."""
    resource_id: str
    resource_type: str  # cache, database_connection, thread_pool
    total_capacity: int
    current_usage: int = 0
    allocation_per_tenant: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def available_capacity(self) -> int:
        """Get available capacity."""
        return max(0, self.total_capacity - self.current_usage)
    
    @property
    def utilization_percent(self) -> float:
        """Get utilization percentage."""
        if self.total_capacity == 0:
            return 0.0
        return (self.current_usage / self.total_capacity) * 100


class StatelessAPIGateway:
    """Stateless API gateway for tenant requests."""
    
    def __init__(self):
        """Initialize API gateway."""
        self.middleware_stack: List[Callable] = []
        self.request_handlers: Dict[str, Callable] = {}
        self.rate_limiters: Dict[str, Dict[str, int]] = {}
    
    def register_middleware(self, middleware: Callable) -> None:
        """Register middleware."""
        self.middleware_stack.append(middleware)
        logger.info(f"Registered middleware: {middleware.__name__}")
    
    def register_handler(self, endpoint: str, handler: Callable) -> None:
        """Register request handler."""
        self.request_handlers[endpoint] = handler
        logger.info(f"Registered handler for {endpoint}")
    
    def extract_tenant(self, request: RequestEnvelope) -> Optional[str]:
        """Extract tenant ID from request."""
        # Try to extract from headers
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # Try to extract from API key
        if request.api_key_prefix:
            # In production, lookup tenant from API key
            return request.metadata.get("tenant_from_api_key")
        
        # Try to extract from custom domain
        host = request.headers.get("Host", "")
        if host != "api.example.com":
            # Custom domain
            return request.metadata.get("tenant_from_domain")
        
        return None
    
    def handle_request(self, request: RequestEnvelope) -> ResponseEnvelope:
        """Handle API request."""
        response = ResponseEnvelope(
            request_id=request.request_id,
            tenant_id=request.tenant_id
        )
        
        try:
            # Extract tenant
            tenant_id = self.extract_tenant(request)
            if not tenant_id and not request.tenant_id:
                response.status = "error"
                response.status_code = 400
                response.errors.append("Tenant ID not found in request")
                return response
            
            request.tenant_id = tenant_id or request.tenant_id
            
            # Apply middleware
            for middleware in self.middleware_stack:
                request = middleware(request)
                if request is None:
                    response.status = "error"
                    response.status_code = 403
                    response.errors.append("Request rejected by middleware")
                    return response
            
            # Get handler
            handler = self.request_handlers.get(request.endpoint)
            if not handler:
                response.status = "error"
                response.status_code = 404
                response.errors.append(f"Handler not found: {request.endpoint}")
                return response
            
            # Execute handler
            start_time = datetime.utcnow()
            result = handler(request)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            response.status = "success"
            response.status_code = 200
            response.data = result
            response.processing_time_ms = int(processing_time)
        
        except Exception as e:
            logger.error(f"Error handling request {request.request_id}: {str(e)}")
            response.status = "error"
            response.status_code = 500
            response.errors.append(f"Internal server error: {str(e)}")
        
        return response


class TenantAwareOrchestrator:
    """Orchestrator with tenant awareness."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.tenant_contexts: Dict[str, List[TenantContext]] = {}
        self.execution_queue: List[Dict[str, Any]] = []
    
    def create_tenant_execution(
        self,
        tenant_id: str,
        app_id: str,
        workflow_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """Create tenant-scoped execution."""
        execution_id = generate_platform_id("orch_exec")
        
        execution = {
            "execution_id": execution_id,
            "tenant_id": tenant_id,
            "app_id": app_id,
            "workflow_id": workflow_id,
            "user_id": user_id,
            "status": "queued",
            "created_at": datetime.utcnow()
        }
        
        self.execution_queue.append(execution)
        
        if tenant_id not in self.tenant_contexts:
            self.tenant_contexts[tenant_id] = []
        
        logger.info(
            f"Created tenant execution: {execution_id} "
            f"({workflow_id}) for tenant {tenant_id}"
        )
        
        return execution_id
    
    def get_tenant_priority_executions(
        self,
        tenant_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get high-priority executions for tenant."""
        tenant_executions = [
            e for e in self.execution_queue
            if e["tenant_id"] == tenant_id and e["status"] == "queued"
        ]
        
        return tenant_executions[:limit]
    
    def route_execution_to_worker(
        self,
        execution_id: str,
        worker_id: str
    ) -> bool:
        """Route execution to worker."""
        for execution in self.execution_queue:
            if execution["execution_id"] == execution_id:
                execution["status"] = "assigned"
                execution["assigned_to"] = worker_id
                logger.info(f"Routed execution {execution_id} to worker {worker_id}")
                return True
        
        return False


class BackgroundWorkerPool:
    """Manages background workers for async processing."""
    
    def __init__(self, num_workers: int = 10):
        """Initialize worker pool."""
        self.num_workers = num_workers
        self.workers: Dict[str, Dict[str, Any]] = {}
        self.job_queue: List[BackgroundJob] = []
        self.completed_jobs: Dict[str, BackgroundJob] = {}
        self._init_workers()
    
    def _init_workers(self) -> None:
        """Initialize worker instances."""
        for i in range(self.num_workers):
            worker_id = generate_platform_id("worker")
            self.workers[worker_id] = {
                "worker_id": worker_id,
                "worker_type": "general",
                "status": "idle",
                "current_job": None,
                "processed_jobs": 0,
                "errors": 0,
                "created_at": datetime.utcnow()
            }
            logger.info(f"Initialized worker: {worker_id}")
    
    def enqueue_job(
        self,
        tenant_id: str,
        job_type: str,
        payload: Dict[str, Any],
        priority: int = 5
    ) -> BackgroundJob:
        """Enqueue background job."""
        job_id = generate_platform_id("job")
        
        job = BackgroundJob(
            job_id=job_id,
            tenant_id=tenant_id,
            job_type=job_type,
            payload=payload,
            priority=priority
        )
        
        # Insert by priority (higher priority first)
        inserted = False
        for i, existing_job in enumerate(self.job_queue):
            if job.priority > existing_job.priority:
                self.job_queue.insert(i, job)
                inserted = True
                break
        
        if not inserted:
            self.job_queue.append(job)
        
        logger.info(f"Enqueued job: {job_id} ({job_type}) for tenant {tenant_id}")
        return job
    
    def assign_jobs_to_workers(self) -> Dict[str, BackgroundJob]:
        """Assign jobs to idle workers."""
        assignments = {}
        
        for worker_id, worker_info in self.workers.items():
            if worker_info["status"] != "idle" or not self.job_queue:
                continue
            
            job = self.job_queue.pop(0)
            job.status = "running"
            job.started_at = datetime.utcnow()
            job.worker_id = worker_id
            
            worker_info["status"] = "busy"
            worker_info["current_job"] = job.job_id
            
            assignments[worker_id] = job
            logger.info(f"Assigned job {job.job_id} to worker {worker_id}")
        
        return assignments
    
    def complete_job(
        self,
        job_id: str,
        result: Dict[str, Any],
        worker_id: Optional[str] = None
    ) -> bool:
        """Mark job as completed."""
        for i, job in enumerate(self.job_queue):
            if job.job_id == job_id:
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.result = result
                
                self.completed_jobs[job_id] = job
                self.job_queue.pop(i)
                
                if worker_id and worker_id in self.workers:
                    self.workers[worker_id]["status"] = "idle"
                    self.workers[worker_id]["processed_jobs"] += 1
                
                logger.info(f"Completed job: {job_id}")
                return True
        
        return False
    
    def fail_job(
        self,
        job_id: str,
        error_message: str,
        worker_id: Optional[str] = None
    ) -> bool:
        """Mark job as failed."""
        for job in self.job_queue:
            if job.job_id == job_id:
                job.retries += 1
                
                if job.retries >= job.max_retries:
                    job.status = "failed"
                    job.error_message = error_message
                    self.completed_jobs[job_id] = job
                    
                    if worker_id and worker_id in self.workers:
                        self.workers[worker_id]["status"] = "idle"
                        self.workers[worker_id]["errors"] += 1
                    
                    logger.error(f"Job failed: {job_id} - {error_message}")
                    return True
                else:
                    # Retry
                    job.status = "queued"
                    job.priority += 1  # Higher priority for retries
                    
                    if worker_id and worker_id in self.workers:
                        self.workers[worker_id]["status"] = "idle"
                    
                    logger.info(f"Retrying job: {job_id} (attempt {job.retries})")
        
        return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get worker pool status."""
        idle_workers = sum(
            1 for w in self.workers.values()
            if w["status"] == "idle"
        )
        
        return {
            "total_workers": self.num_workers,
            "idle_workers": idle_workers,
            "busy_workers": self.num_workers - idle_workers,
            "queued_jobs": len(self.job_queue),
            "completed_jobs": len(self.completed_jobs)
        }


class SharedResourcePool:
    """Manages shared resources for efficient multi-tenant use."""
    
    def __init__(self):
        """Initialize shared resource pool."""
        self.resources: Dict[str, SharedResource] = {}
    
    def create_resource(
        self,
        resource_type: str,
        total_capacity: int
    ) -> SharedResource:
        """Create shared resource."""
        resource_id = generate_platform_id("shared_res")
        
        resource = SharedResource(
            resource_id=resource_id,
            resource_type=resource_type,
            total_capacity=total_capacity
        )
        
        self.resources[resource_id] = resource
        logger.info(
            f"Created shared resource: {resource_id} ({resource_type}) "
            f"with capacity {total_capacity}"
        )
        
        return resource
    
    def allocate_to_tenant(
        self,
        resource_id: str,
        tenant_id: str,
        amount: int
    ) -> bool:
        """Allocate resource to tenant."""
        resource = self.resources.get(resource_id)
        if not resource:
            logger.error(f"Resource not found: {resource_id}")
            return False
        
        # Check capacity
        current_tenant_usage = resource.allocation_per_tenant.get(tenant_id, 0)
        new_total = resource.current_usage - current_tenant_usage + amount
        
        if new_total > resource.total_capacity:
            logger.warning(
                f"Cannot allocate {amount} to tenant {tenant_id}: "
                f"would exceed capacity"
            )
            return False
        
        # Update allocation
        resource.current_usage = new_total
        resource.allocation_per_tenant[tenant_id] = amount
        
        logger.info(
            f"Allocated {amount} units of {resource.resource_type} "
            f"to tenant {tenant_id}"
        )
        
        return True
    
    def get_resource_status(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get resource status."""
        resource = self.resources.get(resource_id)
        if not resource:
            return None
        
        return {
            "resource_id": resource_id,
            "resource_type": resource.resource_type,
            "total_capacity": resource.total_capacity,
            "current_usage": resource.current_usage,
            "available_capacity": resource.available_capacity,
            "utilization_percent": resource.utilization_percent,
            "tenant_allocations": resource.allocation_per_tenant
        }


class PlatformDeploymentManager:
    """Manages platform deployment and scaling."""
    
    def __init__(self):
        """Initialize deployment manager."""
        self.environments: Dict[Environment, EnvironmentConfig] = {}
        self.tenant_configs: Dict[str, TenantEnvironmentConfig] = {}
        self.api_gateway = StatelessAPIGateway()
        self.orchestrator = TenantAwareOrchestrator()
        self.worker_pool = BackgroundWorkerPool(num_workers=20)
        self.resource_pool = SharedResourcePool()
    
    def register_environment(self, config: EnvironmentConfig) -> None:
        """Register deployment environment."""
        self.environments[config.environment] = config
        logger.info(f"Registered environment: {config.environment}")
    
    def create_tenant_config(
        self,
        tenant_id: str,
        custom_domain: Optional[str] = None,
        feature_flags: Optional[Dict[str, bool]] = None
    ) -> TenantEnvironmentConfig:
        """Create tenant environment configuration."""
        config = TenantEnvironmentConfig(
            tenant_id=tenant_id,
            custom_domain=custom_domain,
            feature_flags=feature_flags or {}
        )
        
        self.tenant_configs[tenant_id] = config
        logger.info(f"Created environment config for tenant: {tenant_id}")
        
        return config
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get overall deployment status."""
        return {
            "environments": list(self.environments.keys()),
            "tenant_configs": len(self.tenant_configs),
            "api_gateway": "operational",
            "orchestrator": "operational",
            "worker_pool": self.worker_pool.get_pool_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
