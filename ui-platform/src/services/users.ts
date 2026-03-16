/**
 * Users & RBAC Service
 * User management, roles, permissions, audit
 */

import { apiClient } from './api'

export const usersService = {
  async listUsers() {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/users`)
      return response.data
    } catch (error) {
      console.error('Error fetching users:', error)
      return { users: [] }
    }
  },

  async createUser(data: any) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.post(`/tenants/${tenantId}/users`, data)
      return response.data
    } catch (error) {
      console.error('Error creating user:', error)
      throw error
    }
  },

  async updateUser(userId: string, data: any) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.put(`/tenants/${tenantId}/users/${userId}`, data)
      return response.data
    } catch (error) {
      console.error('Error updating user:', error)
      throw error
    }
  },

  async deleteUser(userId: string) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      await apiClient.delete(`/tenants/${tenantId}/users/${userId}`)
    } catch (error) {
      console.error('Error deleting user:', error)
      throw error
    }
  },

  async generateAPIKey(userId: string) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.post(`/tenants/${tenantId}/api-keys`, {
        user_id: userId,
      })
      return response.data
    } catch (error) {
      console.error('Error generating API key:', error)
      throw error
    }
  },

  async getAuditLogs(limit = 100) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/audit-logs`, {
        params: { limit },
      })
      return response.data
    } catch (error) {
      console.error('Error fetching audit logs:', error)
      return { logs: [] }
    }
  },
}
