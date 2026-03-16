/**
 * usePermission Hook
 * Manages role-based access control and permission checking
 */

import { useState, useEffect, useCallback } from "react";
import { UserRole, userService } from "../services";
import { useAuth } from "./useAuth";

export interface UsePermissionResult {
  hasPermission: (permission: string) => boolean;
  can: (action: string, resource?: string) => boolean;
  isAdmin: boolean;
  isOwner: boolean;
  isLoading: boolean;
  error: string | null;
}

// Role-based permission map
const rolePermissions: Record<UserRole, Set<string>> = {
  owner: new Set([
    "tenant:read",
    "tenant:write",
    "tenant:delete",
    "users:read",
    "users:write",
    "users:delete",
    "apps:read",
    "apps:write",
    "apps:delete",
    "apps:deploy",
    "billing:read",
    "billing:write",
    "metrics:read",
    "rbac:read",
    "rbac:write",
    "api-keys:read",
    "api-keys:write",
    "audit:read",
    "admin:access",
  ]),
  admin: new Set([
    "tenant:read",
    "tenant:write",
    "users:read",
    "users:write",
    "apps:read",
    "apps:write",
    "apps:deploy",
    "billing:read",
    "metrics:read",
    "rbac:read",
    "api-keys:read",
    "api-keys:write",
    "audit:read",
  ]),
  manager: new Set([
    "users:read",
    "apps:read",
    "apps:write",
    "billing:read",
    "metrics:read",
    "api-keys:read",
  ]),
  developer: new Set([
    "apps:read",
    "apps:write",
    "apps:deploy",
    "metrics:read",
    "api-keys:read",
  ]),
  user: new Set([
    "apps:read",
    "metrics:read",
  ]),
  viewer: new Set([
    "tenant:read",
    "apps:read",
    "metrics:read",
  ]),
};

export function usePermission(): UsePermissionResult {
  const { user, isLoading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<Set<string>>(new Set());

  // Load user permissions on mount or when user changes
  useEffect(() => {
    const loadPermissions = async () => {
      if (!user) {
        setPermissions(new Set());
        return;
      }

      setIsLoading(true);
      try {
        const userPermissions = await userService.getPermissions(user.user_id);
        const permSet = new Set(userPermissions.map((p) => `${p.resource_type}:${p.action}`));

        // Also add role-based permissions
        const rolePerms = rolePermissions[user.role] || new Set();
        const combined = new Set([...permSet, ...rolePerms]);

        setPermissions(combined);
        setError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load permissions";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    loadPermissions();
  }, [user]);

  const hasPermission = useCallback(
    (permission: string): boolean => {
      return permissions.has(permission);
    },
    [permissions]
  );

  const can = useCallback(
    (action: string, resource?: string): boolean => {
      const permission = resource ? `${resource}:${action}` : action;
      return hasPermission(permission);
    },
    [hasPermission]
  );

  const isAdmin = user?.role === "admin" || user?.role === "owner";
  const isOwner = user?.role === "owner";

  return {
    hasPermission,
    can,
    isAdmin,
    isOwner,
    isLoading: authLoading || isLoading,
    error,
  };
}
