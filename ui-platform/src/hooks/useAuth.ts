/**
 * Auth Hook
 * Provides authentication state and methods
 */

import { useState, useEffect } from 'react'
import { authService } from '../services/auth'

export const useAuth = () => {
  const [user, setUser] = useState<any>(null)
  const [tenant, setTenant] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const user = authService.getCurrentUser()
    const tenantId = authService.getTenantId()
    if (user.email && tenantId) {
      setUser(user)
      setTenant({ tenant_id: tenantId })
    }
    setLoading(false)
  }, [])

  return {
    user,
    tenant,
    loading,
    isAuthenticated: authService.isAuthenticated(),
    login: authService.login,
    logout: authService.logout,
  }
}
