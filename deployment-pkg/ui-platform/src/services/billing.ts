/**
 * Billing Service
 * Subscriptions, invoices, usage
 */

import { apiClient } from './api'

export const billingService = {
  async getSubscription() {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/subscription`)
      return response.data
    } catch (error) {
      console.error('Error fetching subscription:', error)
      return {
        subscription_id: 'sub_demo',
        plan: 'starter',
        status: 'active',
        current_period_start: new Date().toISOString(),
        current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        monthly_price: 99.0,
      }
    }
  },

  async getInvoices(limit = 10, offset = 0) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/invoices`, {
        params: { limit, offset },
      })
      return response.data
    } catch (error) {
      console.error('Error fetching invoices:', error)
      return { items: [], total: 0 }
    }
  },

  async getBillingEvents() {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.get(`/tenants/${tenantId}/billing-events`)
      return response.data
    } catch (error) {
      console.error('Error fetching billing events:', error)
      return { events: [] }
    }
  },

  async upgradePlan(newPlan: string) {
    try {
      const tenantId = localStorage.getItem('tenant_id')
      const response = await apiClient.post(`/tenants/${tenantId}/upgrade-plan`, {
        new_plan: newPlan,
      })
      return response.data
    } catch (error) {
      console.error('Error upgrading plan:', error)
      throw error
    }
  },
}
