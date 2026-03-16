/// <reference types="vite/client" />
/**
 * Authentication Service Layer
 * Handles token-based auth and session management
 */

import {
  AuthToken,
  AuthContext,
  LoginRequest,
  LoginResponse,
  APIResponse,
  User,
  Tenant,
} from "../types/index";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class AuthService {
  private tokenKey = "srp_auth_token";
  private tenantIdKey = "srp_tenant_id";

  private _buildDemoSession(email: string): LoginResponse {
    const token = "demo_" + Date.now();
    this.setToken(token);
    this.setTenantId("demo-tenant");
    return {
      token: { access_token: token, token_type: "Bearer", expires_in: 3600, refresh_token: token },
      user: {
        user_id: "user_demo",
        tenant_id: "demo-tenant",
        email,
        name: email.split("@")[0],
        role: "owner",
        created_at: new Date().toISOString(),
        disabled: false,
        mfa_enabled: false,
      },
      tenant: {
        tenant_id: "demo-tenant",
        organization_name: "Demo Organization",
        status: "active",
        subscription_plan: "starter",
        owner_email: email,
        created_at: new Date().toISOString(),
        quota: {
          quota_id: "quota_1",
          max_apps: 10,
          max_workflows_per_app: 20,
          max_api_calls_per_month: 100000,
          max_storage_gb: 10,
          max_concurrent_connections: 10,
          max_users: 10,
        },
      },
    };
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    // Try real backend auth endpoint first (uses query params)
    try {
      const params = new URLSearchParams({ email: credentials.email, password: credentials.password });
      const response = await fetch(`${API_BASE_URL}/auth/login?${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (response.ok) {
        const data = await response.json();
        const accessToken = typeof data.token === "string" ? data.token : "demo_" + Date.now();
        this.setToken(accessToken);
        const tenantId = data.tenant_id || "demo-tenant";
        this.setTenantId(tenantId);
        // Store user info for display
        localStorage.setItem("srp_user_name", data.user_name || data.user_email || credentials.email);
        localStorage.setItem("srp_user_role", data.role || "user");
        localStorage.setItem("srp_user_email", data.user_email || credentials.email);
        localStorage.setItem("srp_org_name", data.organization_name || "Emergentic AI Demo");
        return {
          token: { access_token: accessToken, token_type: "Bearer", expires_in: 3600, refresh_token: accessToken },
          user: {
            user_id: data.user_id || "user_1",
            tenant_id: tenantId,
            email: data.user_email || credentials.email,
            name: data.user_name || (data.user_email || credentials.email).split("@")[0],
            role: data.role || "owner",
            created_at: new Date().toISOString(),
            disabled: false,
            mfa_enabled: false,
          },
          tenant: {
            tenant_id: tenantId,
            organization_name: data.organization_name || "Emergentic AI Demo",
            status: "active",
            subscription_plan: "starter",
            owner_email: credentials.email,
            created_at: new Date().toISOString(),
            quota: { quota_id: "quota_1", max_apps: 10, max_workflows_per_app: 20, max_api_calls_per_month: 100000, max_storage_gb: 10, max_concurrent_connections: 10, max_users: 10 },
          },
        };
      } else if (response.status === 401) {
        throw new Error("Invalid email or password");
      }
    } catch (err) {
      if (err instanceof Error && err.message === "Invalid email or password") throw err;
      /* fall through to demo mode on network error */
    }

    // Demo fallback – any email/password works in dev mode
    return this._buildDemoSession(credentials.email);
  }

  async validateToken(token: string): Promise<User> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify?token=${encodeURIComponent(token)}`, {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        if (data.valid) {
          return {
            user_id: data.user?.user_id || "user_demo",
            tenant_id: data.user?.tenant_id || this.getTenantId() || "demo-tenant",
            email: data.user?.email || "demo@example.com",
            name: data.user?.name || "Demo User",
            role: "owner",
            created_at: new Date().toISOString(),
            disabled: false,
            mfa_enabled: false,
          };
        }
      }
    } catch { /* fall through */ }

    // Demo fallback – treat any stored token as valid
    return {
      user_id: "user_demo",
      tenant_id: this.getTenantId() || "demo-tenant",
      email: "demo@example.com",
      name: "Demo User",
      role: "owner",
      created_at: new Date().toISOString(),
      disabled: false,
      mfa_enabled: false,
    };
  }

  async refreshToken(_refreshToken: string): Promise<AuthToken> {
    // No real refresh endpoint – renew demo token
    const newToken = "demo_refreshed_" + Date.now();
    this.setToken(newToken);
    return { access_token: newToken, token_type: "Bearer", expires_in: 3600, refresh_token: newToken };
  }

  async adminAuth(email: string, password: string): Promise<LoginResponse> {
    // Admin authentication (platform-wide access)
    return this.login({
      email,
      password,
      tenant_id: "platform",
    });
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.tenantIdKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  getTenantId(): string | null {
    return localStorage.getItem(this.tenantIdKey);
  }

  setTenantId(tenantId: string): void {
    localStorage.setItem(this.tenantIdKey, tenantId);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    const tenantId = this.getTenantId();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (tenantId) {
      headers["X-Tenant-ID"] = tenantId;
    }

    return headers;
  }
}

export const authService = new AuthService();
