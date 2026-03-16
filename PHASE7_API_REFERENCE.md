"""
PHASE 7 API REFERENCE
====================

Complete API reference for the multi-tenant SaaS platform.
All endpoints require tenant context (from header, domain, or API key).
"""

# ========================================
# 1. TENANT MANAGEMENT API
# ========================================

"""
TENANT PROVISIONING
===================

POST /platform/tenants
  Headers:
    Authorization: Bearer <admin-token>
  Payload:
    organization_name: str
    owner_email: str
    plan: "free" | "starter" | "professional" | "enterprise"
    custom_domain?: str
  Response:
    tenant_id: str
    organization_name: str
    status: "onboarding"
    subscription_plan: str
    created_at: datetime
    onboarding_workflow_id: str

GET /platform/tenants/{tenant_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token> | X-API-Key: <key>
  Response:
    tenant_id: str
    organization_name: str
    status: "onboarding" | "active" | "suspended" | "archived"
    subscription_plan: str
    quota: {
      max_apps: int,
      max_workflows_per_app: int,
      max_api_calls_per_month: int,
      max_storage_gb: int,
      max_concurrent_connections: int,
      max_users: int
    }
    created_at: datetime
    activated_at?: datetime
    custom_domain?: str

PUT /platform/tenants/{tenant_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Payload:
    organization_name?: str
    custom_domain?: str
  Response:
    Success with updated tenant data

POST /platform/tenants/{tenant_id}/activate
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    status: "success"
    message: "Tenant activated"

POST /platform/tenants/{tenant_id}/suspend
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Payload:
    reason?: str
  Response:
    status: "success"
    message: "Tenant suspended"

TENANT QUOTA API
================

GET /platform/tenants/{tenant_id}/quota-usage
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Response:
    apps: {used: int, limit: int, percentage: float}
    workflows: {used: int, limit: int, percentage: float}
    api_calls: {used: int, limit: int, percentage: float}
    storage: {used: float, limit: float, percentage: float}
    concurrent_connections: {used: int, limit: int, percentage: float}
    users: {used: int, limit: int, percentage: float}

POST /platform/tenants/{tenant_id}/record-usage
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <internal-token>
  Payload:
    metric_type: "app_created" | "workflow_created" | "api_call" | "storage" | "connection_active" | "user_added"
    delta: float
  Response:
    status: "success"
    new_usage: float
    percentage: float
    allowed: bool

ONBOARDING API
==============

GET /platform/tenants/{tenant_id}/onboarding
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Response:
    workflow_id: str
    current_phase: str
    progress_percentage: float
    completed_steps: int
    total_steps: int
    steps: [{step_id, name, completed, completed_at?}]

POST /platform/tenants/{tenant_id}/onboarding/steps/{step_id}/complete
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Payload:
    inputs?: dict
  Response:
    status: "success"
    next_phase?: str
    completed: bool
"""

# ========================================
# 2. USER & RBAC API
# ========================================

"""
USER MANAGEMENT
===============

POST /platform/tenants/{tenant_id}/users
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Payload:
    email: str
    name: str
    role: "owner" | "admin" | "manager" | "developer" | "user" | "viewer"
  Response:
    user_id: str
    email: str
    name: str
    role: str
    created_at: datetime

GET /platform/tenants/{tenant_id}/users
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Query:
    limit?: int (default 100)
    offset?: int (default 0)
  Response:
    users: [
      {user_id, email, name, role, created_at, last_login, disabled}
    ]
    total: int

GET /platform/tenants/{tenant_id}/users/{user_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Response:
    user_id: str
    email: str
    name: str
    role: str
    created_at: datetime
    last_login?: datetime
    disabled: bool
    mfa_enabled: bool

PUT /platform/tenants/{tenant_id}/users/{user_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Payload:
    name?: str
    role?: str
    disabled?: bool
    mfa_enabled?: bool
  Response:
    Updated user object

DELETE /platform/tenants/{tenant_id}/users/{user_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    status: "success"

API KEY MANAGEMENT
==================

POST /platform/tenants/{tenant_id}/api-keys
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Payload:
    name: str
    scopes?: ["read", "write"] (default ["read", "write"])
    expires_in_days?: int
  Response:
    key_id: str
    name: str
    key_prefix: str
    created_at: datetime
    expires_at?: datetime
    key_secret: str (only returned once!)

GET /platform/tenants/{tenant_id}/api-keys
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    api_keys: [
      {key_id, name, key_prefix, created_at, last_used, expires_at, revoked}
    ]

DELETE /platform/tenants/{tenant_id}/api-keys/{key_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    status: "success"
    message: "API key revoked"

PERMISSIONS & RBAC
==================

GET /platform/permissions
  Response:
    permissions: [
      {
        permission_id: str,
        name: str,
        resource_type: str,
        action: str,
        description: str
      }
    ]

GET /platform/roles
  Response:
    roles: ["owner", "admin", "manager", "developer", "user", "viewer"]
    role_permissions: {
      "owner": [permission_ids...],
      "admin": [permission_ids...],
      ...
    }

GET /platform/tenants/{tenant_id}/users/{user_id}/permissions
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Response:
    permissions: [permission_ids...]

POST /platform/tenants/{tenant_id}/check-access
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Payload:
    action: str
    resource_type: str
    resource_id?: str
  Response:
    allowed: bool
    reason?: str (if not allowed)

SESSIONS
========

POST /platform/auth/login
  Payload:
    email: str
    password: str
    tenant_id: str
  Response:
    session_id: str
    user_id: str
    tenant_id: str
    token: str (JWT for subsequent requests)
    expires_in_seconds: int

POST /platform/auth/logout
  Headers:
    Authorization: Bearer <token>
  Response:
    status: "success"

GET /platform/auth/session
  Headers:
    Authorization: Bearer <token>
  Response:
    session_id: str
    user_id: str
    tenant_id: str
    created_at: datetime
    last_activity: datetime
    active: bool

AUDIT LOG
=========

GET /platform/tenants/{tenant_id}/audit-logs
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Query:
    limit?: int (default 100)
    offset?: int (default 0)
    action?: str (filter by action)
  Response:
    logs: [
      {
        log_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        status: str,
        changes: dict,
        timestamp: datetime
      }
    ]
    total: int
"""

# ========================================
# 3. BILLING & USAGE API
# ========================================

"""
SUBSCRIPTION MANAGEMENT
=======================

GET /platform/tenants/{tenant_id}/subscription
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    subscription_id: str
    plan: "free" | "starter" | "professional" | "enterprise"
    billing_cycle_start: datetime
    billing_cycle_end: datetime
    auto_renew: bool
    status: "active" | "cancelled" | "suspended"
    current_period_usage: {metric: float}

PUT /platform/tenants/{tenant_id}/subscription
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Payload:
    plan: "free" | "starter" | "professional" | "enterprise"
    auto_renew?: bool
  Response:
    Updated subscription object
    downgrade_credits?: float (if downgrading mid-cycle)

POST /platform/tenants/{tenant_id}/subscription/cancel
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <owner-token>
  Response:
    status: "success"
    cancellation_effective_date: datetime

BILLING & INVOICES
==================

GET /platform/tenants/{tenant_id}/invoices
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Query:
    limit?: int (default 12)
    offset?: int (default 0)
  Response:
    invoices: [
      {
        invoice_id: str,
        period_start: datetime,
        period_end: datetime,
        base_amount: float,
        overage_amount: float,
        tax_amount: float,
        total_amount: float,
        status: "draft" | "issued" | "paid" | "overdue",
        issued_at?: datetime,
        paid_at?: datetime,
        line_items: [{description, amount}]
      }
    ]
    total: int

GET /platform/tenants/{tenant_id}/invoices/{invoice_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    Full invoice detail with PDF URL

GET /platform/tenants/{tenant_id}/billing-summary
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    {
      current_plan: str,
      monthly_cost: float,
      current_usage: {metric: value},
      estimated_overages: float,
      next_billing_date: datetime,
      payment_method: {type, last_4},
      recent_invoices: [...]
    }

USAGE & METRICS
===============

GET /platform/tenants/{tenant_id}/usage
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Query:
    period: "1h" | "1d" | "1m" (default "1d")
  Response:
    {
      apps_created: int,
      workflows_created: int,
      api_calls: int,
      storage_used_gb: float,
      concurrent_connections: int,
      execution_count: int,
      failed_executions: int,
      avg_duration_ms: float,
      total_cost: float,
      period: {start: datetime, end: datetime}
    }

GET /platform/tenants/{tenant_id}/cost-analysis
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Query:
    days?: int (default 30)
  Response:
    {
      total_cost: float,
      daily_costs: [{date, cost}],
      cost_by_metric: {metric: cost},
      projections: {
        daily_average: float,
        monthly_estimate: float,
        annual_estimate: float
      }
    }
"""

# ========================================
# 4. EXECUTION & WORKFLOWS API
# ========================================

"""
WORKFLOW EXECUTION
==================

POST /v1/apps/{app_id}/workflows/{workflow_id}/execute
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token> | X-API-Key: <key>
  Payload:
    input_data: dict
    timeout_seconds?: int (default 300)
  Response:
    execution_id: str
    status: "queued" | "running" | "completed" | "failed"
    started_at: datetime

GET /v1/executions/{execution_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Response:
    execution_id: str
    app_id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at?: datetime
    duration_ms?: int
    input_data: dict
    output_data?: dict
    error_message?: str
    cost: float
    resource_usage: {memory_mb: int, cpu_percent: float}

POST /v1/executions/{execution_id}/cancel
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Response:
    status: "success"
    message: "Execution cancelled"

EXECUTION CONTEXT
=================

GET /platform/tenants/{tenant_id}/executions
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Query:
    limit?: int (default 100)
    status?: str
    app_id?: str
  Response:
    executions: [execution objects]
    total: int

GET /platform/tenants/{tenant_id}/execution-context/{execution_id}
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <internal-token>
  Response:
    {
      execution_id: str,
      variables: dict,
      timeout_seconds: int,
      memory_limit_mb: int,
      created_at: datetime
    }
"""

# ========================================
# 5. OBSERVABILITY & MONITORING API
# ========================================

"""
METRICS
=======

GET /platform/metrics
  Headers:
    Authorization: Bearer <admin-token>
  Query:
    metric_name: str
    tenant_id?: str
    period: "1m" | "5m" | "1h" | "1d" (default "5m")
  Response:
    metric_name: str
    period: {start: datetime, end: datetime}
    data_points: [
      {timestamp: datetime, value: float, tags: dict}
    ]
    aggregates: {
      avg: float,
      max: float,
      min: float,
      sum: float
    }

PLATFORM METRICS
================

GET /platform/health
  Response:
    {
      status: "healthy" | "degraded" | "critical",
      uptime_percent: float,
      response_time_p99_ms: float,
      error_rate_percent: float,
      active_tenants: int,
      active_executions: int,
      worker_pool_utilization: float,
      database_connections: {used: int, total: int},
      cache_hit_rate: float,
      timestamp: datetime
    }

GET /platform/cost-breakdown
  Headers:
    Authorization: Bearer <admin-token>
  Response:
    {
      total_platform_cost: float,
      cost_by_tenant: {tenant_id: float},
      cost_by_metric: {metric: float},
      daily_costs: [{date, cost}],
      trends: {weekly_avg: float, monthly_avg: float}
    }

TENANT METRICS
==============

GET /platform/tenants/{tenant_id}/metrics
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Query:
    period: "1h" | "1d" | "1m" (default "1d")
  Response:
    {
      executions_count: int,
      executions_failed: int,
      success_rate: float,
      avg_duration_ms: float,
      api_calls: int,
      storage_used_gb: float,
      total_cost: float,
      uptime_percent: float,
      period: {start: datetime, end: datetime}
    }

ALERTS
======

GET /platform/alerts
  Headers:
    Authorization: Bearer <admin-token>
  Query:
    tenant_id?: str
    severity?: "info" | "warning" | "critical"
    acknowledged?: bool (default false)
  Response:
    alerts: [
      {
        alert_id: str,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        metric_value: float,
        threshold: float,
        created_at: datetime,
        acknowledged: bool
      }
    ]

POST /platform/alerts/{alert_id}/acknowledge
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <token>
  Response:
    status: "success"

SLA STATUS
==========

GET /platform/sla-status
  Response:
    {
      availability_target: float,
      availability_current: float,
      response_time_target_ms: int,
      response_time_current_ms: float,
      error_rate_target: float,
      error_rate_current: float,
      total_breaches: int,
      compliance_rate: float
    }
"""

# ========================================
# 6. CONFIGURATION API
# ========================================

"""
ENVIRONMENT CONFIG
==================

GET /platform/config/environments
  Headers:
    Authorization: Bearer <admin-token>
  Response:
    {
      environments: ["development", "staging", "production"],
      current: str,
      configs: {
        development: {...},
        staging: {...},
        production: {...}
      }
    }

PUT /platform/config/environments/{environment}
  Headers:
    Authorization: Bearer <admin-token>
  Payload:
    log_level?: str
    enable_profiling?: bool
    enable_debug?: bool
  Response:
    Updated environment config

TENANT CONFIG
=============

GET /platform/tenants/{tenant_id}/config
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    {
      tenant_id: str,
      webhook_url?: str,
      custom_domain?: str,
      feature_flags: {flag_name: bool},
      rate_limits: {endpoint: limit},
      data_retention_days: int,
      backup_frequency: str,
      timezone: str,
      locale: str
    }

PUT /platform/tenants/{tenant_id}/config
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Payload:
    webhook_url?: str
    feature_flags?: dict
    rate_limits?: dict
    timezone?: str
    locale?: str
  Response:
    Updated config

RESOURCE ALLOCATION
===================

GET /platform/tenants/{tenant_id}/resources
  Headers:
    X-Tenant-ID: tenant_id
    Authorization: Bearer <admin-token>
  Response:
    {
      memory_pool: {total_mb: int, used_mb: int, available_mb: int},
      cpu_pool: {total: float, used: float, available: float},
      storage: {total_gb: float, used_gb: float, available_gb: float}
    }
"""

# ========================================
# ERROR RESPONSES
# ========================================

"""
ERROR CODES & RESPONSES
=======================

400 Bad Request
{
  error: "invalid_request",
  message: "descriptive error message",
  details: {...}
}

401 Unauthorized
{
  error: "unauthorized",
  message: "Invalid or missing authentication"
}

403 Forbidden
{
  error: "forbidden",
  message: "Insufficient permissions"
}

404 Not Found
{
  error: "not_found",
  message: "Resource not found"
}

409 Conflict
{
  error: "conflict",
  message: "Resource already exists or state conflict"
}

429 Too Many Requests
{
  error: "rate_limit_exceeded",
  message: "Rate limit exceeded",
  retry_after: int (seconds)
}

500 Internal Server Error
{
  error: "internal_server_error",
  message: "Internal server error"
}
"""

# ========================================
# AUTHENTICATION
# ========================================

"""
AUTHENTICATION METHODS
======================

1. Session/JWT Token
   POST /platform/auth/login
   Returns JWT token
   Use: Authorization: Bearer <token>

2. API Key
   Generate via POST /platform/tenants/{tenant_id}/api-keys
   Use: X-API-Key: <key_prefix>_<key_secret>

3. Tenant Header
   X-Tenant-ID: <tenant_id>
   Combined with session or API key

Common Headers:
  X-Tenant-ID: <tenant_id>                    # Tenant context
  Authorization: Bearer <token>                # Session or API key
  X-Request-ID: <unique_id>                   # For tracing
  Content-Type: application/json              # For POST/PUT

All endpoints require:
  - Valid tenant context (X-Tenant-ID)
  - Valid authentication (Bearer token or API key)
  - Appropriate role/permission
"""

if __name__ == "__main__":
    print("PHASE 7 API REFERENCE\n")
    print("All endpoints require:")
    print("- X-Tenant-ID header or extracted from context")
    print("- Authorization via Bearer token or X-API-Key")
    print("\nSee sections above for complete API documentation")
