/**
 * Apps Service
 * Application management, deployment, logs
 */

import { apiClient } from './api'

export const appsService = {
  async listApps() {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/apps`)
      return response.data
    } catch (error) {
      console.error('Error fetching apps:', error)
      return { apps: [] }
    }
  },

  async getAppDetails(appId: string) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/apps/${appId}`)
      return response.data
    } catch (error) {
      console.error('Error fetching app:', error)
      throw error
    }
  },

  async createApp(data: any) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.post(`/tenants/${tenantId}/apps`, data)
      return response.data
    } catch (error) {
      console.error('Error creating app:', error)
      throw error
    }
  },

  async updateApp(appId: string, data: any) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.put(`/tenants/${tenantId}/apps/${appId}`, data)
      return response.data
    } catch (error) {
      console.error('Error updating app:', error)
      throw error
    }
  },

  async deleteApp(appId: string) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      await apiClient.delete(`/tenants/${tenantId}/apps/${appId}`)
    } catch (error) {
      console.error('Error deleting app:', error)
      throw error
    }
  },

  async getAppLogs(appId: string, limit = 100) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/apps/${appId}/logs`, {
        params: { limit },
      })
      return response.data
    } catch (error) {
      console.error('Error fetching logs:', error)
      return { logs: [] }
    }
  },

  async deployApp(appId: string) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.post(`/tenants/${tenantId}/apps/${appId}/deploy`, {})
      return response.data
    } catch (error) {
      console.error('Error deploying app:', error)
      throw error
    }
  },
}
