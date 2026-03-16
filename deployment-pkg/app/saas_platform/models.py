"""
Core data models for multi-tenant SaaS platform.

Defines tenants, organizations, users, roles, API keys, subscriptions, and billing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from uuid import uuid4


class TenantStatus(str, Enum):
    """Status of a tenant."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    TRIAL = "trial"
    ONBOARDING = "onboarding"


class SubscriptionPlan(str, Enum):
    """Subscription plan tier."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    """User role within organization."""
    ADMIN = "admin"
    OWNER = "owner"
    MANAGER = "manager"
    DEVELOPER = "developer"
    USER = "user"
    VIEWER = "viewer"


class BillingModel(str, Enum):
    """Billing model for subscription."""
    FLAT_RATE = "flat_rate"
    PAY_PER_USE = "pay_per_use"
    HYBRID = "hybrid"


class UsageMetricType(str, Enum):
    """Type of usage metric."""
    APP_GENERATION = "app_generation"
    API_CALLS = "api_calls"
    WORKFLOW_EXECUTIONS = "workflow_executions"
    STORAGE_GB = "storage_gb"
    CONCURRENT_CONNECTIONS = "concurrent_connections"
    CUSTOM_DOMAIN = "custom_domain"
    ADVANCED_ANALYTICS = "advanced_analytics"


class MetricBillingType(str, Enum):
    """How metric is billed."""
    INCLUDED = "included"           # Included in plan
    OVERAGE = "overage"             # Charged per unit above limit
    PREMIUM = "premium"             # Premium feature with per-unit cost


@dataclass
class TenantQuota:
    """Resource quotas for a tenant."""
    quota_id: str
    max_apps: int = 10
    max_workflows_per_app: int = 50
    max_api_calls_per_month: int = 100000
    max_storage_gb: int = 50
    max_concurrent_connections: int = 100
    max_users: int = 5
    max_custom_domains: int = 1
    enable_whitelabel: bool = False
    enable_advanced_analytics: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tenant:
    """Represents a tenant (customer) in the platform."""
    tenant_id: str
    organization_name: str
    status: TenantStatus = TenantStatus.ONBOARDING
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    quota: TenantQuota = field(default_factory=lambda: TenantQuota(quota_id=f"quota_{uuid4().hex[:12]}", max_apps=3))
    owner_email: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    custom_domain: Optional[str] = None
    api_key_secret: Optional[str] = None
    enabled_features: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class User:
    """User within a tenant organization."""
    user_id: str
    tenant_id: str
    email: str
    name: str
    role: UserRole = UserRole.USER
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    disabled: bool = False
    mfa_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIKey:
    """API key for tenant programmatic access."""
    key_id: str
    tenant_id: str
    name: str
    key_prefix: str
    key_hash: str  # Hashed API key
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked: bool = False
    scopes: Set[str] = field(default_factory=set)  # API scopes
    rate_limit_per_minute: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Permission:
    """Permission within an organization."""
    permission_id: str
    name: str
    description: str
    resource_type: str  # apps, workflows, organizations, billing
    action: str  # read, create, update, delete, manage
    org_level: bool = False  # Organization-wide permission


@dataclass
class RolePermissionMapping:
    """Maps roles to permissions."""
    role_id: str
    role: UserRole
    permissions: Set[str] = field(default_factory=set)  # Permission IDs
    custom: bool = False


@dataclass
class UsageMetric:
    """Tracked usage metric for billing."""
    metric_id: str
    tenant_id: str
    metric_type: UsageMetricType
    billing_type: MetricBillingType
    unit: str  # "calls", "gb", "executions", etc.
    value: float
    period: str  # "monthly", "daily", "hourly"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BillingEvent:
    """Billing event for usage tracking."""
    event_id: str
    tenant_id: str
    event_type: str  # app_generated, api_call, workflow_executed, etc.
    quantity: float
    unit_cost: float = 0.0
    total_cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanFeature:
    """Feature definition for a subscription plan."""
    feature_name: str
    included: bool = True
    limit: Optional[int] = None
    unit: Optional[str] = None


@dataclass
class SubscriptionPlanDefinition:
    """Definition of a subscription plan."""
    plan_id: str
    plan_name: SubscriptionPlan
    monthly_price: float
    annual_price: float
    features: Dict[str, PlanFeature] = field(default_factory=dict)
    quotas: TenantQuota = field(default_factory=lambda: TenantQuota(quota_id=f"quota_{uuid4().hex[:12]}"))
    billing_model: BillingModel = BillingModel.FLAT_RATE
    overage_pricing: Dict[str, float] = field(default_factory=dict)  # metric -> price per unit
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    """Active subscription for a tenant."""
    subscription_id: str
    tenant_id: str
    plan: SubscriptionPlan
    billing_cycle_start: datetime
    billing_cycle_end: datetime
    auto_renew: bool = True
    payment_method_id: Optional[str] = None
    status: str = "active"  # active, cancelled, suspended
    current_period_usage: Dict[str, float] = field(default_factory=dict)
    overage_charges: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Invoice:
    """Invoice for a tenant."""
    invoice_id: str
    tenant_id: str
    subscription_id: str
    period_start: datetime
    period_end: datetime
    base_amount: float
    overage_amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    status: str = "draft"  # draft, issued, paid, overdue, cancelled
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantRegistryEntry:
    """Entry in tenant registry for quick lookup."""
    tenant_id: str
    organization_name: str
    custom_domain: Optional[str] = None
    api_key_prefix: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE


@dataclass
class TenantRegistry:
    """Registry for tenant lookups."""
    tenants_by_id: Dict[str, TenantRegistryEntry] = field(default_factory=dict)
    tenants_by_domain: Dict[str, str] = field(default_factory=dict)  # domain -> tenant_id
    tenants_by_api_prefix: Dict[str, str] = field(default_factory=dict)  # api_prefix -> tenant_id
    tenants_by_status: Dict[TenantStatus, Set[str]] = field(default_factory=dict)
    
    def register_tenant(self, entry: TenantRegistryEntry) -> None:
        """Register a tenant."""
        self.tenants_by_id[entry.tenant_id] = entry
        
        if entry.custom_domain:
            self.tenants_by_domain[entry.custom_domain] = entry.tenant_id
        
        if entry.api_key_prefix:
            self.tenants_by_api_prefix[entry.api_key_prefix] = entry.tenant_id
        
        if entry.status not in self.tenants_by_status:
            self.tenants_by_status[entry.status] = set()
        self.tenants_by_status[entry.status].add(entry.tenant_id)
    
    def get_tenant_by_id(self, tenant_id: str) -> Optional[TenantRegistryEntry]:
        """Get tenant by ID."""
        return self.tenants_by_id.get(tenant_id)
    
    def get_tenant_by_domain(self, domain: str) -> Optional[TenantRegistryEntry]:
        """Get tenant by custom domain."""
        tenant_id = self.tenants_by_domain.get(domain)
        return self.tenants_by_id.get(tenant_id) if tenant_id else None
    
    def get_tenant_by_api_key(self, api_key_prefix: str) -> Optional[TenantRegistryEntry]:
        """Get tenant by API key prefix."""
        tenant_id = self.tenants_by_api_prefix.get(api_key_prefix)
        return self.tenants_by_id.get(tenant_id) if tenant_id else None


@dataclass
class TenantContext:
    """Runtime context for tenant execution."""
    tenant_id: str
    tenant: Tenant
    user: Optional[User] = None
    api_key: Optional[APIKey] = None
    request_id: str = field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_authenticated(self) -> bool:
        """Check if context has authentication."""
        return self.user is not None or self.api_key is not None


def generate_platform_id(prefix: str) -> str:
    """Generate unique platform ID with prefix."""
    return f"{prefix}_{uuid4().hex[:12]}"
