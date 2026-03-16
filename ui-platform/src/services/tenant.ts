/**
 * Tenant Service
 * Tenant data, quotas, settings
 */

import { apiClient } from './api'

export const tenantService = {
  async getTenantInfo() {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}`)
      return response.data
    } catch (error) {
      console.error('Error fetching tenant info:', error)
      return {
        tenant_id: localStorage.getItem('tenant_id'),
        organization_name: 'My Organization',
        subscription_plan: 'starter',
        status: 'active',
      }
    }
  },

  async getQuotaUsage() {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/quota`)
      return response.data
    } catch (error) {
      console.error('Error fetching quota:', error)
      return {
        max_apps: 50,
        max_workflows_per_app: 100,
        max_api_calls_per_month: 100000,
        max_storage_gb: 100,
        max_concurrent_connections: 50,
        max_users: 10,
      }
    }
  },

  async updateTenant(data: any) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.put(`/tenants/${tenantId}`, data)
      return response.data
    } catch (error) {
      console.error('Error updating tenant:', error)
      throw error
    }
  },
}
