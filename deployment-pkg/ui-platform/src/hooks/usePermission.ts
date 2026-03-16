/**
 * Permission Hook
 * Check user permissions
 */

import { useAuth } from './useAuth'

const ROLE_PERMISSIONS: Record<string, string[]> = {
  owner: ['all'],
  admin: ['users:manage', 'apps:manage', 'billing:manage', 'settings:manage'],
  manager: ['apps:manage', 'users:view', 'billing:view'],
  developer: ['apps:create', 'apps:deploy', 'workflows:create'],
  user: ['apps:view', 'workflows:view'],
  viewer: ['apps:view'],
}

export const usePermission = () => {
  const { user } = useAuth()

  const can = (permission: string): boolean => {
    if (!user) return false
    const role = user.role || 'viewer'
    const permissions = ROLE_PERMISSIONS[role] || []
    return permissions.includes('all') || permissions.includes(permission)
  }

  return { can }
}
