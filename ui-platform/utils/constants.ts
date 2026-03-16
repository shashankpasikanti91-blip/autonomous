/// <reference types="vite/client" />
/**
 * Constants and Configuration
 * Application-wide constants
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const APP_NAME = "SRP Autonomous OS";
export const APP_TAGLINE = "Enterprise Autonomous AI Platform";

// Subscription Plans
export const SUBSCRIPTION_PLANS = {
  free: {
    name: "Free",
    price: 0,
    description: "For evaluation and small projects",
    features: {
      max_apps: 3,
      max_workflows_per_app: 5,
      max_api_calls_per_month: 10000,
      max_storage_gb: 1,
      max_concurrent_connections: 2,
      max_users: 1,
    },
  },
  starter: {
    name: "Starter",
    price: 49,
    description: "For growing teams and projects",
    features: {
      max_apps: 50,
      max_workflows_per_app: 100,
      max_api_calls_per_month: 1000000,
      max_storage_gb: 50,
      max_concurrent_connections: 10,
      max_users: 5,
    },
  },
  professional: {
    name: "Professional",
    price: 299,
    description: "For production workloads",
    features: {
      max_apps: 500,
      max_workflows_per_app: 1000,
      max_api_calls_per_month: 10000000,
      max_storage_gb: 500,
      max_concurrent_connections: 50,
      max_users: 25,
    },
  },
  enterprise: {
    name: "Enterprise",
    price: null,
    description: "Custom enterprise solutions",
    features: {
      max_apps: "Unlimited",
      max_workflows_per_app: "Unlimited",
      max_api_calls_per_month: "Unlimited",
      max_storage_gb: "Unlimited",
      max_concurrent_connections: "Unlimited",
      max_users: "Unlimited",
    },
  },
};

// User Roles
export const USER_ROLES = {
  owner: { name: "Owner", description: "Full access and control" },
  admin: { name: "Administrator", description: "Manage platform and users" },
  manager: { name: "Manager", description: "Manage apps and users" },
  developer: { name: "Developer", description: "Create and deploy apps" },
  user: { name: "User", description: "Use deployed apps" },
  viewer: { name: "Viewer", description: "View-only access" },
};

// Status Colors
export const STATUS_COLORS = {
  active: "#10b981",
  deployed: "#10b981",
  draft: "#9ca3af",
  paused: "#f59e0b",
  error: "#ef4444",
  suspended: "#f87171",
  onboarding: "#3b82f6",
};

// Alert Severity Colors
export const ALERT_SEVERITY_COLORS = {
  info: "#3b82f6",
  warning: "#f59e0b",
  critical: "#ef4444",
};

// Health Status Colors
export const HEALTH_COLORS = {
  healthy: "#10b981",
  degraded: "#f59e0b",
  critical: "#ef4444",
};

// Polling Intervals (milliseconds)
export const POLLING_INTERVALS = {
  metrics: 30000, // 30 seconds
  health: 60000, // 1 minute
  alerts: 60000, // 1 minute
  usage: 120000, // 2 minutes
};

// Pagination
export const DEFAULT_PAGE_SIZE = 50;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// Timeouts
export const REQUEST_TIMEOUT = 30000; // 30 seconds
export const TOAST_DURATION = 5000; // 5 seconds

// Storage Keys
export const STORAGE_KEYS = {
  auth_token: "srp_auth_token",
  tenant_id: "srp_tenant_id",
  user_preferences: "srp_user_preferences",
  theme: "srp_theme",
};

// Error Messages
export const ERROR_MESSAGES = {
  network_error: "Network error. Please check your connection.",
  server_error: "Server error. Please try again later.",
  unauthorized: "You are not authorized to perform this action.",
  forbidden: "You do not have permission to access this resource.",
  not_found: "The requested resource was not found.",
  validation_error: "Please check your input and try again.",
  quota_exceeded: "You have exceeded your quota for this action.",
};

// Success Messages
export const SUCCESS_MESSAGES = {
  login_success: "Successfully logged in.",
  logout_success: "Successfully logged out.",
  create_success: "Successfully created.",
  update_success: "Successfully updated.",
  delete_success: "Successfully deleted.",
  action_success: "Action completed successfully.",
};

// Date Ranges for Metrics
export const DATE_RANGES = {
  today: { label: "Today", days: 1 },
  week: { label: "Last 7 days", days: 7 },
  month: { label: "Last 30 days", days: 30 },
  quarter: { label: "Last 90 days", days: 90 },
  year: { label: "Last year", days: 365 },
};

// Quota Warning Thresholds (percentage)
export const QUOTA_WARNING_THRESHOLDS = {
  low: 50,
  medium: 75,
  high: 90,
  critical: 95,
};

export type SubscriptionPlanType = keyof typeof SUBSCRIPTION_PLANS;
export type UserRoleType = keyof typeof USER_ROLES;
export type DateRangeType = keyof typeof DATE_RANGES;
