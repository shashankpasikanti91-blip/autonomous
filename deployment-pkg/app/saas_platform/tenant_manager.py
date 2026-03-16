"""
Tenant management system for multi-tenant SaaS platform.

Handles tenant registration, configuration, quotas, isolation, and lifecycle.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
import logging
from enum import Enum

from saas_platform.models import (
    Tenant, TenantStatus, SubscriptionPlan, TenantQuota, TenantRegistry,
    TenantRegistryEntry, generate_platform_id, User, UserRole, APIKey
)


logger = logging.getLogger(__name__)


class OnboardingPhase(str, Enum):
    """Phase of tenant onboarding."""
    VERIFICATION = "verification"
    SETUP = "setup"
    CONFIGURATION = "configuration"
    TESTING = "testing"
    ACTIVATION = "activation"
    COMPLETED = "completed"


@dataclass
class OnboardingStep:
    """Step in tenant onboarding workflow."""
    step_id: str
    phase: OnboardingPhase
    name: str
    description: str
    required_inputs: Dict[str, str] = field(default_factory=dict)
    validation_rules: List[Callable[[Any], bool]] = field(default_factory=list)
    completed: bool = False
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OnboardingWorkflow:
    """Workflow for tenant onboarding."""
    workflow_id: str
    tenant_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    current_phase: OnboardingPhase = OnboardingPhase.VERIFICATION
    steps: List[OnboardingStep] = field(default_factory=list)
    completed_steps: int = 0
    total_steps: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress_percentage(self) -> float:
        """Get onboarding progress percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100


@dataclass
class TenantResourceUsage:
    """Current resource usage for a tenant."""
    tenant_id: str
    apps_created: int = 0
    workflows_created: int = 0
    api_calls_this_month: int = 0
    storage_used_gb: float = 0.0
    active_connections: int = 0
    users_created: int = 0
    custom_domains_used: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuotaExceededAlert:
    """Alert when quota is exceeded."""
    alert_id: str
    tenant_id: str
    quota_name: str
    current_value: float
    limit: float
    percentage_over: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantIsolationPolicy:
    """Policy for tenant isolation."""
    policy_id: str
    tenant_id: str
    network_isolated: bool = True
    storage_isolated: bool = True
    compute_isolated: bool = True
    credential_isolated: bool = True
    execution_timeout_seconds: int = 300
    memory_limit_mb: int = 1024
    cpu_allocation_percent: int = 50
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantManager:
    """Manages tenant lifecycle and operations."""
    
    def __init__(self):
        """Initialize tenant manager."""
        self.registry = TenantRegistry()
        self.tenants: Dict[str, Tenant] = {}
        self.usage: Dict[str, TenantResourceUsage] = {}
        self.onboarding: Dict[str, OnboardingWorkflow] = {}
        self.isolation_policies: Dict[str, TenantIsolationPolicy] = {}
        self.quota_alerts: Dict[str, List[QuotaExceededAlert]] = {}
    
    def create_tenant(
        self,
        organization_name: str,
        owner_email: str,
        plan: SubscriptionPlan = SubscriptionPlan.FREE,
        custom_domain: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Create new tenant."""
        tenant_id = generate_platform_id("tenant")
        
        # Create quota based on plan
        quota = self._create_quota_for_plan(plan)
        
        # Create tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            organization_name=organization_name,
            subscription_plan=plan,
            quota=quota,
            owner_email=owner_email,
            custom_domain=custom_domain,
            status=TenantStatus.ONBOARDING,
            metadata=metadata or {}
        )
        
        self.tenants[tenant_id] = tenant
        self.usage[tenant_id] = TenantResourceUsage(tenant_id=tenant_id)
        self.quota_alerts[tenant_id] = []
        
        # Create isolation policy
        self.isolation_policies[tenant_id] = TenantIsolationPolicy(
            policy_id=generate_platform_id("policy"),
            tenant_id=tenant_id
        )
        
        # Register in registry
        entry = TenantRegistryEntry(
            tenant_id=tenant_id,
            organization_name=organization_name,
            custom_domain=custom_domain,
            status=TenantStatus.ONBOARDING,
            subscription_plan=plan
        )
        self.registry.register_tenant(entry)
        
        logger.info(f"Created tenant: {tenant_id} ({organization_name})")
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)
    
    def activate_tenant(self, tenant_id: str) -> bool:
        """Activate a tenant."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            return False
        
        tenant.status = TenantStatus.ACTIVE
        tenant.activated_at = datetime.utcnow()
        
        # Update registry
        if tenant_id in self.registry.tenants_by_id:
            entry = self.registry.tenants_by_id[tenant_id]
            entry.status = TenantStatus.ACTIVE
        
        logger.info(f"Activated tenant: {tenant_id}")
        return True
    
    def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """Suspend a tenant."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            return False
        
        tenant.status = TenantStatus.SUSPENDED
        tenant.suspended_at = datetime.utcnow()
        tenant.metadata["suspension_reason"] = reason
        
        # Update registry
        if tenant_id in self.registry.tenants_by_id:
            entry = self.registry.tenants_by_id[tenant_id]
            entry.status = TenantStatus.SUSPENDED
        
        logger.info(f"Suspended tenant: {tenant_id} - Reason: {reason}")
        return True
    
    def archive_tenant(self, tenant_id: str) -> bool:
        """Archive a tenant."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            return False
        
        tenant.status = TenantStatus.ARCHIVED
        tenant.metadata["archived_at"] = datetime.utcnow().isoformat()
        
        # Update registry
        if tenant_id in self.registry.tenants_by_id:
            entry = self.registry.tenants_by_id[tenant_id]
            entry.status = TenantStatus.ARCHIVED
        
        logger.info(f"Archived tenant: {tenant_id}")
        return True
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by custom domain."""
        entry = self.registry.get_tenant_by_domain(domain)
        return self.tenants.get(entry.tenant_id) if entry else None
    
    def get_tenant_by_api_key(self, api_key_prefix: str) -> Optional[Tenant]:
        """Get tenant by API key prefix."""
        entry = self.registry.get_tenant_by_api_key(api_key_prefix)
        return self.tenants.get(entry.tenant_id) if entry else None
    
    def upgrade_subscription(
        self,
        tenant_id: str,
        new_plan: SubscriptionPlan
    ) -> bool:
        """Upgrade tenant subscription plan."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            return False
        
        old_plan = tenant.subscription_plan
        tenant.subscription_plan = new_plan
        tenant.quota = self._create_quota_for_plan(new_plan)
        tenant.metadata["plan_upgraded_from"] = old_plan.value
        tenant.metadata["plan_upgraded_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Upgraded tenant {tenant_id} from {old_plan} to {new_plan}")
        return True
    
    def check_quota_usage(self, tenant_id: str) -> Dict[str, Dict[str, Any]]:
        """Check quota usage for tenant."""
        tenant = self.tenants.get(tenant_id)
        usage = self.usage.get(tenant_id)
        
        if not tenant or not usage:
            logger.error(f"Tenant or usage not found: {tenant_id}")
            return {}
        
        usage_report = {
            "apps": {
                "used": usage.apps_created,
                "limit": tenant.quota.max_apps,
                "percentage": (usage.apps_created / tenant.quota.max_apps * 100) if tenant.quota.max_apps > 0 else 0
            },
            "workflows": {
                "used": usage.workflows_created,
                "limit": tenant.quota.max_workflows_per_app,
                "percentage": (usage.workflows_created / tenant.quota.max_workflows_per_app * 100) if tenant.quota.max_workflows_per_app > 0 else 0
            },
            "api_calls": {
                "used": usage.api_calls_this_month,
                "limit": tenant.quota.max_api_calls_per_month,
                "percentage": (usage.api_calls_this_month / tenant.quota.max_api_calls_per_month * 100) if tenant.quota.max_api_calls_per_month > 0 else 0
            },
            "storage": {
                "used": usage.storage_used_gb,
                "limit": tenant.quota.max_storage_gb,
                "percentage": (usage.storage_used_gb / tenant.quota.max_storage_gb * 100) if tenant.quota.max_storage_gb > 0 else 0
            },
            "connections": {
                "used": usage.active_connections,
                "limit": tenant.quota.max_concurrent_connections,
                "percentage": (usage.active_connections / tenant.quota.max_concurrent_connections * 100) if tenant.quota.max_concurrent_connections > 0 else 0
            },
            "users": {
                "used": usage.users_created,
                "limit": tenant.quota.max_users,
                "percentage": (usage.users_created / tenant.quota.max_users * 100) if tenant.quota.max_users > 0 else 0
            }
        }
        
        return usage_report
    
    def record_usage(
        self,
        tenant_id: str,
        metric_type: str,
        delta: float = 1.0
    ) -> bool:
        """Record usage metric."""
        usage = self.usage.get(tenant_id)
        if not usage:
            logger.error(f"Tenant usage not found: {tenant_id}")
            return False
        
        if metric_type == "app_created":
            usage.apps_created += int(delta)
        elif metric_type == "workflow_created":
            usage.workflows_created += int(delta)
        elif metric_type == "api_call":
            usage.api_calls_this_month += int(delta)
        elif metric_type == "storage":
            usage.storage_used_gb += delta
        elif metric_type == "connection_active":
            usage.active_connections += int(delta)
        elif metric_type == "user_added":
            usage.users_created += int(delta)
        
        usage.last_updated = datetime.utcnow()
        
        # Check quotas
        self._check_and_alert_quotas(tenant_id)
        
        return True
    
    def create_onboarding_workflow(self, tenant_id: str) -> OnboardingWorkflow:
        """Create onboarding workflow for tenant."""
        workflow_id = generate_platform_id("onboard")
        
        workflow = OnboardingWorkflow(
            workflow_id=workflow_id,
            tenant_id=tenant_id
        )
        
        # Create steps
        steps = [
            OnboardingStep(
                step_id=generate_platform_id("step"),
                phase=OnboardingPhase.VERIFICATION,
                name="Email Verification",
                description="Verify owner email address",
                required_inputs={"email": "Owner email"}
            ),
            OnboardingStep(
                step_id=generate_platform_id("step"),
                phase=OnboardingPhase.SETUP,
                name="Organization Setup",
                description="Configure organization name and basic settings",
                required_inputs={"org_name": "Organization name"}
            ),
            OnboardingStep(
                step_id=generate_platform_id("step"),
                phase=OnboardingPhase.CONFIGURATION,
                name="Feature Configuration",
                description="Enable and configure features based on plan",
                required_inputs={}
            ),
            OnboardingStep(
                step_id=generate_platform_id("step"),
                phase=OnboardingPhase.TESTING,
                name="API Testing",
                description="Test API integration",
                required_inputs={}
            ),
            OnboardingStep(
                step_id=generate_platform_id("step"),
                phase=OnboardingPhase.ACTIVATION,
                name="Tenant Activation",
                description="Activate tenant in production",
                required_inputs={}
            )
        ]
        
        workflow.steps = steps
        workflow.total_steps = len(steps)
        
        self.onboarding[workflow_id] = workflow
        
        logger.info(f"Created onboarding workflow for tenant: {tenant_id}")
        return workflow
    
    def complete_onboarding_step(
        self,
        workflow_id: str,
        step_id: str
    ) -> bool:
        """Mark onboarding step as completed."""
        workflow = self.onboarding.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return False
        
        for step in workflow.steps:
            if step.step_id == step_id:
                step.completed = True
                step.completed_at = datetime.utcnow()
                workflow.completed_steps += 1
                
                # Move to next phase if all steps done
                if workflow.completed_steps == workflow.total_steps:
                    workflow.current_phase = OnboardingPhase.COMPLETED
                    # Activate tenant
                    self.activate_tenant(workflow.tenant_id)
                
                logger.info(f"Completed onboarding step: {step_id}")
                return True
        
        return False
    
    def get_onboarding_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding status."""
        workflow = self.onboarding.get(workflow_id)
        if not workflow:
            return None
        
        return {
            "workflow_id": workflow_id,
            "tenant_id": workflow.tenant_id,
            "current_phase": workflow.current_phase.value,
            "progress_percentage": workflow.progress_percentage,
            "completed_steps": workflow.completed_steps,
            "total_steps": workflow.total_steps,
            "started_at": workflow.started_at.isoformat(),
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "completed": step.completed,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None
                }
                for step in workflow.steps
            ]
        }
    
    def get_isolation_policy(self, tenant_id: str) -> Optional[TenantIsolationPolicy]:
        """Get isolation policy for tenant."""
        return self.isolation_policies.get(tenant_id)
    
    def update_isolation_policy(
        self,
        tenant_id: str,
        **kwargs
    ) -> Optional[TenantIsolationPolicy]:
        """Update isolation policy for tenant."""
        policy = self.isolation_policies.get(tenant_id)
        if not policy:
            logger.error(f"Policy not found for tenant: {tenant_id}")
            return None
        
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        logger.info(f"Updated isolation policy for tenant: {tenant_id}")
        return policy
    
    def _create_quota_for_plan(self, plan: SubscriptionPlan) -> TenantQuota:
        """Create quota based on subscription plan."""
        quotas = {
            SubscriptionPlan.FREE: TenantQuota(
                quota_id=generate_platform_id("quota"),
                max_apps=3,
                max_workflows_per_app=10,
                max_api_calls_per_month=10000,
                max_storage_gb=5,
                max_concurrent_connections=10,
                max_users=1,
                max_custom_domains=0
            ),
            SubscriptionPlan.STARTER: TenantQuota(
                quota_id=generate_platform_id("quota"),
                max_apps=20,
                max_workflows_per_app=50,
                max_api_calls_per_month=100000,
                max_storage_gb=50,
                max_concurrent_connections=50,
                max_users=5,
                max_custom_domains=1,
                enable_advanced_analytics=False
            ),
            SubscriptionPlan.PROFESSIONAL: TenantQuota(
                quota_id=generate_platform_id("quota"),
                max_apps=100,
                max_workflows_per_app=200,
                max_api_calls_per_month=1000000,
                max_storage_gb=500,
                max_concurrent_connections=200,
                max_users=25,
                max_custom_domains=5,
                enable_whitelabel=False,
                enable_advanced_analytics=True
            ),
            SubscriptionPlan.ENTERPRISE: TenantQuota(
                quota_id=generate_platform_id("quota"),
                max_apps=10000,
                max_workflows_per_app=10000,
                max_api_calls_per_month=100000000,
                max_storage_gb=10000,
                max_concurrent_connections=5000,
                max_users=500,
                max_custom_domains=100,
                enable_whitelabel=True,
                enable_advanced_analytics=True
            )
        }
        
        return quotas.get(plan, quotas[SubscriptionPlan.FREE])
    
    def _check_and_alert_quotas(self, tenant_id: str) -> None:
        """Check quotas and generate alerts."""
        usage_report = self.check_quota_usage(tenant_id)
        
        for metric, data in usage_report.items():
            percentage = data.get("percentage", 0)
            
            # Alert at 80% and 95%
            if percentage >= 95:
                if not self._has_recent_alert(tenant_id, metric, 95):
                    alert = QuotaExceededAlert(
                        alert_id=generate_platform_id("alert"),
                        tenant_id=tenant_id,
                        quota_name=metric,
                        current_value=data["used"],
                        limit=data["limit"],
                        percentage_over=percentage
                    )
                    self.quota_alerts[tenant_id].append(alert)
                    logger.warning(f"Quota alert for tenant {tenant_id}: {metric} at {percentage:.1f}%")
            elif percentage >= 80:
                if not self._has_recent_alert(tenant_id, metric, 80):
                    alert = QuotaExceededAlert(
                        alert_id=generate_platform_id("alert"),
                        tenant_id=tenant_id,
                        quota_name=metric,
                        current_value=data["used"],
                        limit=data["limit"],
                        percentage_over=percentage
                    )
                    self.quota_alerts[tenant_id].append(alert)
                    logger.info(f"Quota warning for tenant {tenant_id}: {metric} at {percentage:.1f}%")
    
    def _has_recent_alert(
        self,
        tenant_id: str,
        metric: str,
        threshold: float,
        hours: int = 24
    ) -> bool:
        """Check if recent alert exists for metric."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        for alert in self.quota_alerts.get(tenant_id, []):
            if (alert.quota_name == metric and
                alert.percentage_over >= threshold and
                alert.triggered_at > cutoff):
                return True
        
        return False


class TenantIsolationManager:
    """Manages tenant isolation enforcement."""
    
    def __init__(self, tenant_manager: TenantManager):
        """Initialize isolation manager."""
        self.tenant_manager = tenant_manager
    
    def validate_tenant_access(
        self,
        tenant_id: str,
        resource_tenant_id: str
    ) -> bool:
        """Validate if tenant can access resource."""
        # Tenant can only access its own resources
        return tenant_id == resource_tenant_id
    
    def enforce_resource_limits(
        self,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Enforce resource limits for tenant."""
        policy = self.tenant_manager.get_isolation_policy(tenant_id)
        if not policy:
            return {}
        
        return {
            "execution_timeout": policy.execution_timeout_seconds,
            "memory_limit_mb": policy.memory_limit_mb,
            "cpu_allocation_percent": policy.cpu_allocation_percent,
            "network_isolated": policy.network_isolated,
            "storage_isolated": policy.storage_isolated
        }
    
    def isolate_tenant_data(
        self,
        tenant_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensure tenant data isolation."""
        return {
            "tenant_id": tenant_id,
            "data": data,
            "isolated_at": datetime.utcnow().isoformat(),
            "isolation_level": "strict"
        }
