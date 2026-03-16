/**
 * Tenant Hook
 * Provides tenant data and utilities
 */

import { useState, useEffect } from 'react'
import { tenantService } from '../services/tenant'

export const useTenant = () => {
  const [tenantInfo, setTenantInfo] = useState<any>(null)
  const [quota, setQuota] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTenantData = async () => {
      try {
        const [info, quotaData] = await Promise.all([
          tenantService.getTenantInfo(),
          tenantService.getQuotaUsage(),
        ])
        setTenantInfo(info)
        setQuota(quotaData)
      } finally {
        setLoading(false)
      }
    }

    loadTenantData()
  }, [])

  return {
    tenantInfo,
    quota,
    loading,
  }
}
