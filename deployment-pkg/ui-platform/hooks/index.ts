/**
 * Hooks Barrel Export
 * Central export point for all custom React hooks
 */

export { useAuth, useAuthState, AuthProvider } from "./useAuth";
export type { AuthContextType } from "./useAuth";

export { useTenant, useTenantState, TenantProvider } from "./useTenant";
export type { TenantContextType } from "./useTenant";

export { useMetrics } from "./useMetrics";
export type { UseMetricsOptions, UseMetricsResult } from "./useMetrics";

export { usePermission } from "./usePermission";
export type { UsePermissionResult } from "./usePermission";
