/**
 * SRP Autonomous OS - TypeScript Type Definitions
 * Complete type system for enterprise platform
 */

// ========================================
// TENANT TYPES
// ========================================

export type TenantStatus = "onboarding" | "active" | "suspended" | "archived";
export type SubscriptionPlan = "free" | "starter" | "professional" | "enterprise";

export interface Tenant {
  tenant_id: string;
  organization_name: string;
  status: TenantStatus;
  subscription_plan: SubscriptionPlan;
  owner_email: string;
  created_at: string;
  activated_at?: string;
  custom_domain?: string;
  quota: TenantQuota;
}

export interface TenantQuota {
  quota_id: string;
  max_apps: number;
  max_workflows_per_app: number;
  max_api_calls_per_month: number;
  max_storage_gb: number;
  max_concurrent_connections: number;
  max_users: number;
}

// ========================================
// USER & RBAC TYPES
// ========================================

export type UserRole = "owner" | "admin" | "manager" | "developer" | "user" | "viewer";

export interface User {
  user_id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
  last_login?: string;
  disabled: boolean;
  mfa_enabled: boolean;
}

export interface APIKey {
  key_id: string;
  tenant_id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used?: string;
  expires_at?: string;
  revoked: boolean;
  scopes: string[];
}

export interface Permission {
  permission_id: string;
  name: string;
  resource_type: string;
  action: string;
  description: string;
}

export interface UserSession {
  session_id: string;
  user_id: string;
  tenant_id: string;
  created_at: string;
  last_activity: string;
  active: boolean;
}

// ========================================
// BILLING TYPES
// ========================================

export interface Subscription {
  subscription_id: string;
  tenant_id: string;
  plan: SubscriptionPlan;
  billing_cycle_start: string;
  billing_cycle_end: string;
  auto_renew: boolean;
  status: "active" | "cancelled" | "suspended";
  current_period_usage: Record<string, number>;
}

export interface Invoice {
  invoice_id: string;
  tenant_id: string;
  period_start: string;
  period_end: string;
  base_amount: number;
  overage_amount: number;
  tax_amount: number;
  total_amount: number;
  status: "draft" | "issued" | "paid" | "overdue";
  issued_at?: string;
  paid_at?: string;
  line_items: LineItem[];
}

export interface LineItem {
  description: string;
  amount: number;
}

export interface BillingEvents {
  total_executions: number;
  failed_executions: number;
  api_calls: number;
  storage_used_gb: number;
  success_rate: number;
  avg_execution_duration_ms: number;
  total_cost: number;
}

// ========================================
// APP & WORKFLOW TYPES
// ========================================

export interface App {
  app_id: string;
  tenant_id: string;
  name: string;
  description?: string;
  version: string;
  status: "draft" | "deployed" | "paused" | "error";
  created_at: string;
  created_by: string;
  last_modified: string;
  workflow_count: number;
  execution_count: number;
}

export interface AppExecution {
  execution_id: string;
  app_id: string;
  workflow_id: string;
  status: "queued" | "running" | "completed" | "failed";
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  cost: number;
  error_message?: string;
}

export interface AppMetrics {
  total_executions: number;
  failed_executions: number;
  avg_duration_ms: number;
  total_cost: number;
  success_rate: number;
  peak_concurrent: number;
  last_execution?: string;
}

// ========================================
// METRICS & OBSERVABILITY TYPES
// ========================================

export interface PlatformMetric {
  metric_name: string;
  value: number;
  unit: string;
  timestamp: string;
  tags?: Record<string, string>;
}

export interface TenantMetrics {
  tenant_id: string;
  period_start: string;
  period_end: string;
  executions_count: number;
  executions_failed: number;
  success_rate: number;
  avg_execution_duration_ms: number;
  api_calls_total: number;
  storage_used_gb: number;
  total_cost: number;
  uptime_percent: number;
}

export interface ExecutionMetric {
  execution_id: string;
  tenant_id: string;
  app_id: string;
  status: string;
  duration_ms: number;
  memory_used_mb: number;
  cpu_used_percent: number;
  cost: number;
  timestamp: string;
}

export interface PlatformHealth {
  status: "healthy" | "degraded" | "critical";
  uptime_percent: number;
  response_time_p99_ms: number;
  error_rate_percent: number;
  active_tenants: number;
  active_executions: number;
  worker_pool_utilization: number;
  database_connections: {
    used: number;
    total: number;
  };
  cache_hit_rate: number;
  timestamp: string;
}

export interface Alert {
  alert_id: string;
  alert_type: string;
  severity: "info" | "warning" | "critical";
  tenant_id?: string;
  title: string;
  description: string;
  metric_value: number;
  threshold: number;
  created_at: string;
  acknowledged: boolean;
}

// ========================================
// DASHBOARD TYPES
// ========================================

export interface DashboardData {
  tenant?: Tenant;
  user?: User;
  metrics?: TenantMetrics;
  health?: PlatformHealth;
  recent_executions?: AppExecution[];
  alerts?: Alert[];
  subscription?: Subscription;
}

export interface QuotaUsage {
  apps: QuotaMetric;
  workflows: QuotaMetric;
  api_calls: QuotaMetric;
  storage: QuotaMetric;
  concurrent_connections: QuotaMetric;
  users: QuotaMetric;
}

export interface QuotaMetric {
  used: number;
  limit: number;
  percentage: number;
}

export interface UsageBreakdown {
  period_start: string;
  period_end: string;
  apps_created: number;
  workflows_created: number;
  api_calls: number;
  storage_used_gb: number;
  executions: number;
  failed_executions: number;
  total_cost: number;
}

// ========================================
// API RESPONSE TYPES
// ========================================

export interface APIResponse<T> {
  status: "success" | "error";
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  timestamp: string;
  request_id: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ========================================
// AUTH TYPES
// ========================================

export interface AuthToken {
  access_token: string;
  token_type: "Bearer";
  expires_in: number;
  refresh_token?: string;
}

export interface AuthContext {
  user: User | null;
  tenant: Tenant | null;
  token: string | null;
  is_authenticated: boolean;
  has_permission: (permission: string) => boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
  tenant_id?: string;
}

export interface LoginResponse {
  user: User;
  tenant: Tenant;
  token: AuthToken;
}

// ========================================
// UI STATE TYPES
// ========================================

export interface UIState {
  loading: boolean;
  error: string | null;
  success: string | null;
}

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
}

export interface FilterState {
  search?: string;
  status?: string;
  date_range?: {
    start: string;
    end: string;
  };
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface NotificationMessage {
  id: string;
  type: "success" | "error" | "warning" | "info";
  message: string;
  duration?: number;
}

// ========================================
// PLAN & PRICING TYPES
// ========================================

export interface PricingPlan {
  plan_id: string;
  name: SubscriptionPlan;
  monthly_price: number;
  annual_price: number;
  features: Record<string, PlanFeature>;
  description?: string;
}

export interface PlanFeature {
  included: boolean;
  limit?: number;
  unit?: string;
}

// ========================================
// AUDIT & LOGGING
// ========================================

export interface AuditLogEntry {
  log_id: string;
  tenant_id: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id: string;
  status: "success" | "failure";
  error_message?: string;
  changes: Record<string, unknown>;
  timestamp: string;
  ip_address?: string;
}

// ========================================
// REPORT TYPES
// ========================================

export interface CostReport {
  period: {
    start: string;
    end: string;
  };
  total_cost: number;
  daily_costs: Array<{
    date: string;
    cost: number;
  }>;
  cost_by_metric: Record<string, number>;
  projections: {
    daily_average: number;
    monthly_estimate: number;
    annual_estimate: number;
  };
}

export interface UsageReport {
  period: {
    start: string;
    end: string;
  };
  metrics: Record<string, number>;
  trends: Array<{
    date: string;
    metric: string;
    value: number;
  }>;
}
