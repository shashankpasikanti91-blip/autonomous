"""
Multi-tenant SaaS platform layer for Emergentic AI.

Provides comprehensive enterprise platformization on top of Phase 4, 5, and 6:
- Phase 4: Integration & service adapters (hardened)
- Phase 5: Autonomous intelligence & agent orchestration
- Phase 6: Prompt-to-app generation and runtime

Phase 7 adds:
- Multi-tenant registry and isolation
- RBAC with users, roles, permissions
- Billing, metering, and subscription management
- Tenant resource isolation and quotas
- Stateless SaaS API architecture
- Platform observability and monitoring
"""

# Core data models
from saas_platform.models import (
    TenantStatus,
    SubscriptionPlan,
    UserRole,
    BillingModel,
    UsageMetricType,
    MetricBillingType,
    Tenant,
    TenantQuota,
    User,
    APIKey,
    Permission,
    RolePermissionMapping,
    UsageMetric,
    BillingEvent,
    Subscription,
    Invoice,
    SubscriptionPlanDefinition,
    TenantRegistryEntry,
    TenantRegistry,
    TenantContext,
    generate_platform_id,
)

# Tenant management
from saas_platform.tenant_manager import (
    OnboardingPhase,
    OnboardingStep,
    OnboardingWorkflow,
    TenantResourceUsage,
    QuotaExceededAlert,
    TenantIsolationPolicy,
    TenantManager,
    TenantIsolationManager,
)

# RBAC and authentication
from saas_platform.rbac_engine import (
    PermissionManager,
    UserManager,
    APIKeyManager,
    SessionManager,
    AuditLogger,
    AuthorizationEngine,
    RBACPolicy,
    UserSession,
    AuditLogEntry,
)

# Billing and metering
from saas_platform.billing_engine import (
    BillingCalculator,
    UsageTracker,
    BillingEventLogger,
    QuotaEnforcer,
    InvoiceGenerator,
    BillingEngine,
)

# Runtime isolation
from saas_platform.runtime_isolation import (
    TenantExecutionContext,
    TenantResourcePool,
    TenantIntegrationCredential,
    TenantWorkflowExecution,
    TenantInstance,
    TenantExecutionIsolationManager,
    TenantResourcePoolManager,
    TenantCredentialManager,
    TenantWorkflowExecutionTracker,
    TenantInstanceManager,
)

# SaaS deployment
from saas_platform.saas_deployment import (
    Environment,
    WorkerType,
    EnvironmentConfig,
    TenantEnvironmentConfig,
    RequestEnvelope,
    ResponseEnvelope,
    BackgroundJob,
    SharedResource,
    StatelessAPIGateway,
    TenantAwareOrchestrator,
    BackgroundWorkerPool,
    SharedResourcePool,
    PlatformDeploymentManager,
)

# Platform observability
from saas_platform.observability import (
    Metric,
    MetricWindow,
    ExecutionMetrics,
    TenantMetrics,
    Alert,
    PlatformHealthStatus,
    AuditLog,
    MetricsCollector,
    ExecutionCostTracker,
    SLAMonitor,
    PlatformHealthDashboard,
    AlertManager,
    AuditLogger as PlatformAuditLogger,
)


class PlatformCore:
    """Core platform initialization and orchestration."""
    
    def __init__(self):
        """Initialize platform core."""
        # Tenant management
        self.tenant_manager = TenantManager()
        self.tenant_isolation = TenantIsolationManager(self.tenant_manager)
        
        # RBAC and security
        self.permission_manager = PermissionManager()
        self.user_manager = UserManager(self.permission_manager)
        self.api_key_manager = APIKeyManager()
        self.session_manager = SessionManager()
        self.rbac_audit_logger = AuditLogger()
        self.authorization_engine = AuthorizationEngine(
            self.permission_manager,
            self.user_manager,
            self.rbac_audit_logger
        )
        
        # Billing and metering
        self.billing_engine = BillingEngine()
        
        # Runtime isolation
        self.execution_isolation = TenantExecutionIsolationManager()
        self.resource_pool_manager = TenantResourcePoolManager()
        self.credential_manager = TenantCredentialManager()
        self.execution_tracker = TenantWorkflowExecutionTracker()
        self.instance_manager = TenantInstanceManager()
        
        # SaaS deployment
        self.deployment_manager = PlatformDeploymentManager()
        
        # Observability
        self.metrics_collector = MetricsCollector()
        self.cost_tracker = ExecutionCostTracker()
        self.sla_monitor = SLAMonitor()
        self.health_dashboard = PlatformHealthDashboard(
            self.metrics_collector,
            self.cost_tracker,
            self.sla_monitor
        )
        self.alert_manager = AlertManager()
        self.platform_audit_logger = PlatformAuditLogger()
    
    def provision_tenant(
        self,
        organization_name: str,
        owner_email: str,
        plan: SubscriptionPlan = SubscriptionPlan.FREE,
        custom_domain: str = None
    ) -> Tenant:
        """Provision new tenant."""
        # Create tenant
        tenant = self.tenant_manager.create_tenant(
            organization_name=organization_name,
            owner_email=owner_email,
            plan=plan,
            custom_domain=custom_domain
        )
        
        # Create subscription
        self.billing_engine.create_subscription(
            tenant_id=tenant.tenant_id,
            plan=plan
        )
        
        # Create resource pool
        self.resource_pool_manager.create_resource_pool(
            tenant_id=tenant.tenant_id
        )
        
        # Create onboarding workflow
        onboarding = self.tenant_manager.create_onboarding_workflow(
            tenant_id=tenant.tenant_id
        )
        
        # Create environment config
        self.deployment_manager.create_tenant_config(
            tenant_id=tenant.tenant_id,
            custom_domain=custom_domain
        )
        
        # Log audit event
        self.platform_audit_logger.log_action(
            action="tenant_created",
            resource_type="tenant",
            resource_id=tenant.tenant_id,
            changes={"plan": plan.value}
        )
        
        return tenant
    
    def add_user_to_tenant(
        self,
        tenant_id: str,
        email: str,
        name: str,
        role: UserRole = UserRole.USER
    ) -> User:
        """Add user to tenant."""
        user = self.user_manager.create_user(
            tenant_id=tenant_id,
            email=email,
            name=name,
            role=role
        )
        
        # Log audit event
        self.platform_audit_logger.log_action(
            action="user_added",
            resource_type="user",
            resource_id=user.user_id,
            tenant_id=tenant_id,
            changes={"role": role.value}
        )
        
        return user
    
    def execute_workflow(
        self,
        tenant_id: str,
        app_id: str,
        workflow_id: str,
        user_id: str,
        input_data: dict = None
    ) -> str:
        """Execute workflow for tenant."""
        # Check authorization
        if not self.authorization_engine.check_access(
            user_id,
            "execute",
            "workflows",
            workflow_id,
            tenant_id
        ):
            raise Exception(f"User {user_id} not authorized to execute workflow")
        
        # Create execution context
        execution = self.execution_isolation.create_execution_context(
            tenant_id=tenant_id,
            user_id=user_id,
            app_id=app_id,
            workflow_id=workflow_id,
            variables=input_data or {}
        )
        
        # Start workflow execution tracking
        wf_execution = self.execution_tracker.start_execution(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            app_id=app_id,
            triggered_by=user_id,
            input_data=input_data
        )
        
        # Record usage
        self.billing_engine.record_usage(
            tenant_id=tenant_id,
            metric_type=UsageMetricType.WORKFLOW_EXECUTIONS,
            value=1.0
        )
        
        # Log audit event
        self.platform_audit_logger.log_action(
            action="workflow_executed",
            resource_type="workflow",
            resource_id=workflow_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return wf_execution.execution_id
    
    def get_billing_summary(self, tenant_id: str) -> dict:
        """Get tenant billing summary."""
        return self.billing_engine.get_billing_summary(tenant_id)
    
    def get_platform_status(self) -> dict:
        """Get platform status."""
        health = self.health_dashboard.get_platform_health()
        
        return {
            "platform": {
                "status": health.status,
                "uptime_percent": health.uptime_percent,
                "response_time_p99_ms": health.response_time_p99_ms,
                "error_rate_percent": health.error_rate_percent
            },
            "deployment": self.deployment_manager.get_deployment_status(),
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_tenant_status(self, tenant_id: str) -> dict:
        """Get tenant status."""
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {}
        
        usage = self.tenant_manager.check_quota_usage(tenant_id)
        health = self.health_dashboard.get_tenant_health(tenant_id)
        
        return {
            "tenant": {
                "id": tenant_id,
                "name": tenant.organization_name,
                "status": tenant.status.value,
                "plan": tenant.subscription_plan.value
            },
            "usage": usage,
            "health": health,
            "timestamp": datetime.utcnow().isoformat()
        }


# Platform instance factory
def create_platform_instance() -> PlatformCore:
    """Create platform instance."""
    return PlatformCore()


__all__ = [
    # Platform core
    "PlatformCore",
    "create_platform_instance",
    
    # Models
    "TenantStatus",
    "SubscriptionPlan",
    "UserRole",
    "BillingModel",
    "UsageMetricType",
    "Tenant",
    "User",
    "APIKey",
    "Subscription",
    "Invoice",
    "TenantContext",
    
    # Tenant management
    "TenantManager",
    "TenantIsolationManager",
    "OnboardingWorkflow",
    "TenantResourceUsage",
    
    # RBAC
    "PermissionManager",
    "UserManager",
    "APIKeyManager",
    "SessionManager",
    "AuthorizationEngine",
    
    # Billing
    "BillingEngine",
    "BillingCalculator",
    "UsageTracker",
    "QuotaEnforcer",
    
    # Runtime
    "TenantExecutionIsolationManager",
    "TenantResourcePoolManager",
    "TenantCredentialManager",
    "TenantInstanceManager",
    
    # SaaS
    "PlatformDeploymentManager",
    "StatelessAPIGateway",
    "BackgroundWorkerPool",
    
    # Observability
    "MetricsCollector",
    "ExecutionCostTracker",
    "SLAMonitor",
    "PlatformHealthDashboard",
    "AlertManager",
]


from datetime import datetime
