/**
 * User Management & RBAC Service Layer
 * Handles user management, roles, permissions, and API keys
 */

import {
  User,
  UserRole,
  APIKey,
  Permission,
  AuditLogEntry,
  APIResponse,
  PaginatedResponse,
} from "../types/index";
import { authService } from "./auth";

class UserService {
  private _demoUser(userId = "user_demo"): User {
    return {
      user_id: userId,
      tenant_id: authService.getTenantId() || "demo-tenant",
      email: "demo@example.com",
      name: "Demo User",
      role: "owner" as UserRole,
      created_at: "2024-01-01T00:00:00Z",
      disabled: false,
      mfa_enabled: false,
    } as User;
  }

  async getCurrentUser(): Promise<User> {
    return this._demoUser();
  }

  async getUser(userId: string): Promise<User> {
    return this._demoUser(userId);
  }

  async listUsers(
    _tenantId?: string,
    limit = 50,
    offset = 0
  ): Promise<PaginatedResponse<User>> {
    return { items: [this._demoUser()], total: 1, limit, offset };
  }

  async createUser(
    _tenantId: string,
    userData: Partial<User>
  ): Promise<User> {
    return { ...this._demoUser(), ...userData } as User;
  }

  async updateUser(userId: string, updates: Partial<User>): Promise<User> {
    return { ...this._demoUser(userId), ...updates } as User;
  }

  async deleteUser(_userId: string): Promise<void> {
    // no-op: no real endpoint
  }

  async assignRole(userId: string, role: UserRole): Promise<User> {
    return this.updateUser(userId, { role });
  }

  async disableUser(userId: string): Promise<User> {
    return this.updateUser(userId, { disabled: true });
  }

  async enableUser(userId: string): Promise<User> {
    return this.updateUser(userId, { disabled: false });
  }

  async getPermissions(_userId: string): Promise<Permission[]> {
    return [];
  }

  async checkPermission(
    _userId: string,
    _permission: string
  ): Promise<boolean> {
    return true;
  }

  async listAPIKeys(
    _tenantId?: string,
    limit = 50,
    offset = 0
  ): Promise<PaginatedResponse<APIKey>> {
    return { items: [], total: 0, limit, offset };
  }

  async createAPIKey(
    _tenantId: string,
    keyData: Partial<APIKey>
  ): Promise<APIKey> {
    return { key_id: `key_${Date.now()}`, key_value: "demo_key", created_at: new Date().toISOString(), ...keyData } as APIKey;
  }

  async revokeAPIKey(keyId: string): Promise<APIKey> {
    return { key_id: keyId, revoked: true } as APIKey;
  }

  async getAuditLogs(
    _tenantId?: string,
    limit = 100,
    offset = 0
  ): Promise<PaginatedResponse<AuditLogEntry>> {
    return { items: [], total: 0, limit, offset };
  }

  async enableMFA(_userId: string): Promise<{ secret: string; qr_code: string }> {
    return { secret: "DEMO_MFA_SECRET", qr_code: "demo_qr_code" };
  }

  async disableMFA(_userId: string): Promise<void> {
    // no-op: no real endpoint
  }
}

export const userService = new UserService();
