/**
 * Metrics Hook
 * Provides metrics and health data
 */

import { useState, useEffect } from 'react'
import { metricsService } from '../services/metrics'

export const useMetrics = () => {
  const [tenantMetrics, setTenantMetrics] = useState<any>(null)
  const [platformHealth, setPlatformHealth] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const [metrics, health] = await Promise.all([
          metricsService.getTenantMetrics(),
          metricsService.getPlatformHealth(),
        ])
        setTenantMetrics(metrics)
        setPlatformHealth(health)
      } finally {
        setIsLoading(false)
      }
    }

    loadMetrics()
    // Refresh every 30 seconds
    const interval = setInterval(loadMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  return {
    tenantMetrics,
    platformHealth,
    isLoading,
  }
}
