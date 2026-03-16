/**
 * Tenant Service Layer
 * Handles tenant management and provisioning
 */

import { Tenant, APIResponse, PaginatedResponse, TenantQuota } from "../types/index";
import { authService } from "./auth";

class TenantService {
  private _demoTenant(): Tenant {
    const tenantId = authService.getTenantId() || "demo-tenant";
    return {
      tenant_id: tenantId,
      organization_name: "Demo Organization",
      status: "active",
      subscription_plan: "starter",
      owner_email: "admin@demo.com",
      created_at: "2024-01-01T00:00:00Z",
      quota: {
        quota_id: "quota_1",
        max_apps: 10,
        max_workflows_per_app: 20,
        max_api_calls_per_month: 100000,
        max_storage_gb: 10,
        max_concurrent_connections: 10,
        max_users: 10,
      },
    };
  }

  async getCurrentTenant(): Promise<Tenant> {
    // No real /platform/ui/tenant endpoint – return demo data
    return this._demoTenant();
  }

  async getTenant(_tenantId: string): Promise<Tenant> {
    return this._demoTenant();
  }

  async listTenants(
    _limit = 50,
    _offset = 0
  ): Promise<PaginatedResponse<Tenant>> {
    return { items: [this._demoTenant()], total: 1, limit: _limit, offset: _offset };
  }

  async createTenant(tenantData: Partial<Tenant>): Promise<Tenant> {
    return { ...this._demoTenant(), ...tenantData } as Tenant;
  }

  async updateTenant(_tenantId: string, updates: Partial<Tenant>): Promise<Tenant> {
    return { ...this._demoTenant(), ...updates } as Tenant;
  }

  async suspendTenant(tenantId: string): Promise<Tenant> {
    return this.updateTenant(tenantId, { status: "suspended" });
  }

  async activateTenant(tenantId: string): Promise<Tenant> {
    return this.updateTenant(tenantId, { status: "active" });
  }

  async getQuota(_tenantId?: string): Promise<TenantQuota> {
    return {
      quota_id: "quota_1",
      max_apps: 10,
      max_workflows_per_app: 20,
      max_api_calls_per_month: 100000,
      max_storage_gb: 10,
      max_concurrent_connections: 10,
      max_users: 10,
    };
  }

  async updateQuota(
    _tenantId: string,
    quota: Partial<TenantQuota>
  ): Promise<TenantQuota> {
    return {
      quota_id: "quota_1",
      max_apps: 10,
      max_workflows_per_app: 20,
      max_api_calls_per_month: 100000,
      max_storage_gb: 10,
      max_concurrent_connections: 10,
      max_users: 10,
      ...quota,
    } as TenantQuota;
  }

  async getTenantStats(_tenantId: string): Promise<Record<string, unknown>> {
    return { agents: 4, workflows: 6, executions: 0, events: 0 };
  }
}

export const tenantService = new TenantService();
