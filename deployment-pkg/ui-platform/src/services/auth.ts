/**
 * Authentication Service
 * Handle login, logout, token management
 */

import { apiClient } from './api'

export interface LoginCredentials {
  email: string
  password: string
  tenant_id?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: string
  tenant_id: string
  email: string
  name: string
  role: string
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/login', credentials)
    const data = response.data
    
    // Store token
    localStorage.setItem('auth_token', data.access_token)
    localStorage.setItem('tenant_id', data.tenant_id)
    localStorage.setItem('user_id', data.user_id)
    localStorage.setItem('user_email', data.email)
    localStorage.setItem('user_name', data.name)
    localStorage.setItem('user_role', data.role)
    
    return data
  },

  async logout() {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('tenant_id')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_email')
    localStorage.removeItem('user_name')
    localStorage.removeItem('user_role')
  },

  getToken(): string | null {
    return localStorage.getItem('auth_token')
  },

  getTenantId(): string | null {
    return localStorage.getItem('tenant_id')
  },

  getCurrentUser() {
    return {
      id: localStorage.getItem('user_id'),
      email: localStorage.getItem('user_email'),
      name: localStorage.getItem('user_name'),
      role: localStorage.getItem('user_role'),
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token')
  },
}
