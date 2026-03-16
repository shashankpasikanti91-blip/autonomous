"""
Multi-tenant runtime isolation for secure tenant execution.

Ensures tenant data, workflows, and resources are properly isolated.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import logging

from saas_platform.models import TenantContext, generate_platform_id


logger = logging.getLogger(__name__)


@dataclass
class TenantExecutionContext:
    """Execution context for tenant operations."""
    execution_id: str
    tenant_id: str
    user_id: Optional[str] = None
    app_id: Optional[str] = None
    workflow_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    timeout_seconds: int = 300
    memory_limit_mb: int = 1024
    allowed_ip_ranges: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantResourcePool:
    """Resource pool for tenant."""
    pool_id: str
    tenant_id: str
    total_memory_mb: int = 10240
    used_memory_mb: int = 0
    total_cpu_percent: int = 100
    used_cpu_percent: int = 0
    max_concurrent_executions: int = 50
    active_executions: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def available_memory_mb(self) -> int:
        """Get available memory."""
        return max(0, self.total_memory_mb - self.used_memory_mb)
    
    @property
    def memory_utilization_percent(self) -> float:
        """Get memory utilization percentage."""
        if self.total_memory_mb == 0:
            return 0.0
        return (self.used_memory_mb / self.total_memory_mb) * 100
    
    @property
    def cpu_utilization_percent(self) -> float:
        """Get CPU utilization percentage."""
        if self.total_cpu_percent == 0:
            return 0.0
        return (self.used_cpu_percent / self.total_cpu_percent) * 100


@dataclass
class TenantIntegrationCredential:
    """Isolated credential for tenant integration."""
    credential_id: str
    tenant_id: str
    integration_name: str
    api_key: str  # Encrypted
    api_secret: str  # Encrypted
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_rotated: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantWorkflowExecution:
    """Execution record for tenant workflow."""
    execution_id: str
    tenant_id: str
    workflow_id: str
    app_id: str
    triggered_by: str  # user_id or api_key_id
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    steps_executed: int = 0
    steps_total: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantInstance:
    """Instance of an application running as tenant."""
    instance_id: str
    tenant_id: str
    app_id: str
    version: str
    status: str = "running"  # running, paused, stopped, error
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    resource_allocation: Dict[str, int] = field(default_factory=dict)
    current_load: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantExecutionIsolationManager:
    """Manages execution isolation for tenants."""
    
    def __init__(self):
        """Initialize execution isolation manager."""
        self.execution_contexts: Dict[str, TenantExecutionContext] = {}
        self.tenant_contexts: Dict[str, List[str]] = {}
    
    def create_execution_context(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        timeout_seconds: int = 300,
        memory_limit_mb: int = 1024,
        variables: Optional[Dict[str, Any]] = None,
        secrets: Optional[Dict[str, str]] = None
    ) -> TenantExecutionContext:
        """Create isolated execution context."""
        execution_id = generate_platform_id("exec")
        
        context = TenantExecutionContext(
            execution_id=execution_id,
            tenant_id=tenant_id,
            user_id=user_id,
            app_id=app_id,
            workflow_id=workflow_id,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=memory_limit_mb,
            variables=variables or {},
            secrets=secrets or {}
        )
        
        self.execution_contexts[execution_id] = context
        
        if tenant_id not in self.tenant_contexts:
            self.tenant_contexts[tenant_id] = []
        self.tenant_contexts[tenant_id].append(execution_id)
        
        logger.info(f"Created execution context: {execution_id} for tenant {tenant_id}")
        return context
    
    def get_execution_context(self, execution_id: str) -> Optional[TenantExecutionContext]:
        """Get execution context."""
        return self.execution_contexts.get(execution_id)
    
    def validate_execution_access(
        self,
        execution_id: str,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Validate access to execution context."""
        context = self.get_execution_context(execution_id)
        if not context:
            return False
        
        # Tenant must match
        if context.tenant_id != tenant_id:
            logger.warning(
                f"Tenant mismatch for execution {execution_id}: "
                f"requested {tenant_id}, context {context.tenant_id}"
            )
            return False
        
        # User must match if specified
        if user_id and context.user_id and context.user_id != user_id:
            logger.warning(
                f"User mismatch for execution {execution_id}: "
                f"requested {user_id}, context {context.user_id}"
            )
            return False
        
        return True
    
    def inject_variable(
        self,
        execution_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Inject variable into execution context."""
        context = self.get_execution_context(execution_id)
        if not context:
            logger.error(f"Execution context not found: {execution_id}")
            return False
        
        context.variables[key] = value
        return True
    
    def get_tenant_executions(
        self,
        tenant_id: str,
        limit: int = 100
    ) -> List[TenantExecutionContext]:
        """Get execution contexts for tenant."""
        execution_ids = self.tenant_contexts.get(tenant_id, [])
        
        # Return most recent executions
        executions = [
            self.execution_contexts[eid]
            for eid in execution_ids[-limit:]
            if eid in self.execution_contexts
        ]
        
        return list(reversed(executions))


class TenantResourcePoolManager:
    """Manages resource pools for tenants."""
    
    def __init__(self):
        """Initialize resource pool manager."""
        self.resource_pools: Dict[str, TenantResourcePool] = {}
    
    def create_resource_pool(
        self,
        tenant_id: str,
        total_memory_mb: int = 10240,
        total_cpu_percent: int = 100,
        max_concurrent_executions: int = 50
    ) -> TenantResourcePool:
        """Create resource pool for tenant."""
        pool_id = generate_platform_id("pool")
        
        pool = TenantResourcePool(
            pool_id=pool_id,
            tenant_id=tenant_id,
            total_memory_mb=total_memory_mb,
            total_cpu_percent=total_cpu_percent,
            max_concurrent_executions=max_concurrent_executions
        )
        
        self.resource_pools[pool_id] = pool
        
        logger.info(f"Created resource pool: {pool_id} for tenant {tenant_id}")
        return pool
    
    def get_tenant_resource_pool(self, tenant_id: str) -> Optional[TenantResourcePool]:
        """Get resource pool for tenant."""
        for pool in self.resource_pools.values():
            if pool.tenant_id == tenant_id:
                return pool
        return None
    
    def allocate_resources(
        self,
        tenant_id: str,
        memory_mb: int,
        cpu_percent: int,
        duration_seconds: int
    ) -> Optional[str]:
        """Allocate resources for execution."""
        pool = self.get_tenant_resource_pool(tenant_id)
        if not pool:
            logger.error(f"Resource pool not found for tenant: {tenant_id}")
            return None
        
        # Check availability
        if pool.used_memory_mb + memory_mb > pool.total_memory_mb:
            logger.warning(
                f"Insufficient memory in pool for tenant {tenant_id}: "
                f"required {memory_mb}MB, available {pool.available_memory_mb}MB"
            )
            return None
        
        if pool.used_cpu_percent + cpu_percent > pool.total_cpu_percent:
            logger.warning(
                f"Insufficient CPU in pool for tenant {tenant_id}: "
                f"required {cpu_percent}%, available {pool.total_cpu_percent - pool.used_cpu_percent}%"
            )
            return None
        
        if pool.active_executions >= pool.max_concurrent_executions:
            logger.warning(
                f"Max concurrent executions reached for tenant {tenant_id}"
            )
            return None
        
        # Allocate
        allocation_id = generate_platform_id("alloc")
        pool.used_memory_mb += memory_mb
        pool.used_cpu_percent += cpu_percent
        pool.active_executions += 1
        
        logger.info(
            f"Allocated resources for tenant {tenant_id}: "
            f"{memory_mb}MB memory, {cpu_percent}% CPU"
        )
        
        return allocation_id
    
    def release_resources(
        self,
        tenant_id: str,
        memory_mb: int,
        cpu_percent: int
    ) -> bool:
        """Release allocated resources."""
        pool = self.get_tenant_resource_pool(tenant_id)
        if not pool:
            logger.error(f"Resource pool not found for tenant: {tenant_id}")
            return False
        
        pool.used_memory_mb = max(0, pool.used_memory_mb - memory_mb)
        pool.used_cpu_percent = max(0, pool.used_cpu_percent - cpu_percent)
        pool.active_executions = max(0, pool.active_executions - 1)
        
        logger.info(
            f"Released resources for tenant {tenant_id}: "
            f"{memory_mb}MB memory, {cpu_percent}% CPU"
        )
        
        return True
    
    def get_pool_health(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get health status of tenant resource pool."""
        pool = self.get_tenant_resource_pool(tenant_id)
        if not pool:
            return None
        
        return {
            "pool_id": pool.pool_id,
            "memory": {
                "total": pool.total_memory_mb,
                "used": pool.used_memory_mb,
                "available": pool.available_memory_mb,
                "utilization_percent": pool.memory_utilization_percent
            },
            "cpu": {
                "total": pool.total_cpu_percent,
                "used": pool.used_cpu_percent,
                "available": pool.total_cpu_percent - pool.used_cpu_percent,
                "utilization_percent": pool.cpu_utilization_percent
            },
            "executions": {
                "active": pool.active_executions,
                "max_concurrent": pool.max_concurrent_executions
            }
        }


class TenantCredentialManager:
    """Manages encrypted credentials per tenant."""
    
    def __init__(self):
        """Initialize credential manager."""
        self.credentials: Dict[str, TenantIntegrationCredential] = {}
        self.tenant_credentials: Dict[str, Set[str]] = {}
    
    def store_credential(
        self,
        tenant_id: str,
        integration_name: str,
        api_key: str,
        api_secret: str,
        expires_in_days: Optional[int] = None
    ) -> TenantIntegrationCredential:
        """Store encrypted credential for tenant."""
        credential_id = generate_platform_id("cred")
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        credential = TenantIntegrationCredential(
            credential_id=credential_id,
            tenant_id=tenant_id,
            integration_name=integration_name,
            api_key=api_key,  # In production, encrypt this
            api_secret=api_secret,  # In production, encrypt this
            expires_at=expires_at
        )
        
        self.credentials[credential_id] = credential
        
        if tenant_id not in self.tenant_credentials:
            self.tenant_credentials[tenant_id] = set()
        self.tenant_credentials[tenant_id].add(credential_id)
        
        logger.info(
            f"Stored credential for tenant {tenant_id}: {integration_name}"
        )
        
        return credential
    
    def get_credential(
        self,
        tenant_id: str,
        integration_name: str
    ) -> Optional[TenantIntegrationCredential]:
        """Get credential for tenant integration."""
        credential_ids = self.tenant_credentials.get(tenant_id, set())
        
        for cred_id in credential_ids:
            credential = self.credentials.get(cred_id)
            if (credential and
                credential.integration_name == integration_name and
                (not credential.expires_at or credential.expires_at > datetime.utcnow())):
                return credential
        
        return None
    
    def rotate_credential(
        self,
        credential_id: str,
        new_api_key: str,
        new_api_secret: str
    ) -> bool:
        """Rotate credential."""
        credential = self.credentials.get(credential_id)
        if not credential:
            logger.error(f"Credential not found: {credential_id}")
            return False
        
        credential.api_key = new_api_key
        credential.api_secret = new_api_secret
        credential.last_rotated = datetime.utcnow()
        
        logger.info(f"Rotated credential: {credential_id}")
        return True
    
    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke credential."""
        credential = self.credentials.get(credential_id)
        if not credential:
            logger.error(f"Credential not found: {credential_id}")
            return False
        
        credential.expires_at = datetime.utcnow()
        
        logger.info(f"Revoked credential: {credential_id}")
        return True


class TenantWorkflowExecutionTracker:
    """Tracks workflow executions per tenant."""
    
    def __init__(self):
        """Initialize workflow execution tracker."""
        self.executions: Dict[str, TenantWorkflowExecution] = {}
        self.tenant_executions: Dict[str, List[str]] = {}
    
    def start_execution(
        self,
        tenant_id: str,
        workflow_id: str,
        app_id: str,
        triggered_by: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> TenantWorkflowExecution:
        """Start workflow execution."""
        execution_id = generate_platform_id("wfexec")
        
        execution = TenantWorkflowExecution(
            execution_id=execution_id,
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            app_id=app_id,
            triggered_by=triggered_by,
            status="running",
            started_at=datetime.utcnow(),
            input_data=input_data or {}
        )
        
        self.executions[execution_id] = execution
        
        if tenant_id not in self.tenant_executions:
            self.tenant_executions[tenant_id] = []
        self.tenant_executions[tenant_id].append(execution_id)
        
        logger.info(
            f"Started workflow execution: {execution_id} "
            f"({workflow_id}) for tenant {tenant_id}"
        )
        
        return execution
    
    def complete_execution(
        self,
        execution_id: str,
        output_data: Dict[str, Any],
        steps_executed: int = 0,
        steps_total: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Complete workflow execution."""
        execution = self.executions.get(execution_id)
        if not execution:
            logger.error(f"Execution not found: {execution_id}")
            return False
        
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int(
            (execution.completed_at - execution.started_at).total_seconds() * 1000
        )
        execution.output_data = output_data
        execution.steps_executed = steps_executed
        execution.steps_total = steps_total
        
        if error_message:
            execution.status = "failed"
            execution.error_message = error_message
        else:
            execution.status = "completed"
        
        logger.info(
            f"Completed workflow execution: {execution_id} "
            f"(status: {execution.status}, duration: {execution.duration_ms}ms)"
        )
        
        return True
    
    def get_tenant_executions(
        self,
        tenant_id: str,
        limit: int = 100
    ) -> List[TenantWorkflowExecution]:
        """Get workflow executions for tenant."""
        execution_ids = self.tenant_executions.get(tenant_id, [])
        
        executions = [
            self.executions[eid]
            for eid in execution_ids[-limit:]
            if eid in self.executions
        ]
        
        return list(reversed(executions))


class TenantInstanceManager:
    """Manages application instances per tenant."""
    
    def __init__(self):
        """Initialize instance manager."""
        self.instances: Dict[str, TenantInstance] = {}
        self.tenant_instances: Dict[str, List[str]] = {}
    
    def create_instance(
        self,
        tenant_id: str,
        app_id: str,
        version: str
    ) -> TenantInstance:
        """Create application instance for tenant."""
        instance_id = generate_platform_id("inst")
        
        instance = TenantInstance(
            instance_id=instance_id,
            tenant_id=tenant_id,
            app_id=app_id,
            version=version
        )
        
        self.instances[instance_id] = instance
        
        if tenant_id not in self.tenant_instances:
            self.tenant_instances[tenant_id] = []
        self.tenant_instances[tenant_id].append(instance_id)
        
        logger.info(
            f"Created instance: {instance_id} ({app_id}:{version}) "
            f"for tenant {tenant_id}"
        )
        
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[TenantInstance]:
        """Get instance."""
        return self.instances.get(instance_id)
    
    def get_tenant_instances(self, tenant_id: str) -> List[TenantInstance]:
        """Get instances for tenant."""
        instance_ids = self.tenant_instances.get(tenant_id, [])
        return [
            self.instances[iid]
            for iid in instance_ids
            if iid in self.instances
        ]
    
    def update_instance_health(
        self,
        instance_id: str,
        status: str = "running",
        load: float = 0.0,
        error_message: Optional[str] = None
    ) -> bool:
        """Update instance health."""
        instance = self.get_instance(instance_id)
        if not instance:
            logger.error(f"Instance not found: {instance_id}")
            return False
        
        instance.status = status
        instance.current_load = load
        instance.last_heartbeat = datetime.utcnow()
        
        if error_message:
            instance.error_messages.append(error_message)
            if len(instance.error_messages) > 10:
                instance.error_messages = instance.error_messages[-10:]
        
        return True
