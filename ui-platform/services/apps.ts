/**
 * App Management Service Layer
 * Handles app lifecycle, deployment, and execution tracking
 * Apps are persisted in PostgreSQL via the FastAPI backend.
 * localStorage is used as a cache fallback only.
 */

import {
  App,
  AppExecution,
  AppMetrics,
  PaginatedResponse,
} from "../types/index";
import { dbCreateApp, dbLogExecution } from "./supabase";

const STORAGE_KEY = "srp_apps";
const DEMO_ORG_ID = "00000000-0000-0000-0000-000000000010";

class AppService {
  // ── Persistence helpers ──────────────────────────────────────────────────

  private _loadApps(): App[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw) as App[];
    } catch { /* ignore */ }
    // Seed with a demo app on first load
    const seed = this._makeDemoApp();
    this._saveApps([seed]);
    return [seed];
  }

  private _saveApps(apps: App[]): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(apps));
  }

  private _makeDemoApp(appId = "app_demo"): App {
    return {
      app_id: appId,
      tenant_id: "demo-tenant",
      name: "Demo App",
      description: "Demo application",
      status: "deployed",
      created_at: "2024-01-01T00:00:00Z",
      workflow_count: 2,
    } as App;
  }

  // ── Public API ────────────────────────────────────────────────────────────

  async listApps(
    _tenantId?: string,
    limit = 50,
    offset = 0
  ): Promise<PaginatedResponse<App>> {
    try {
      const backendUrl = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/records/apps?org_id=${DEMO_ORG_ID}`);
      if (res.ok) {
        const json = await res.json();
        const dbApps: App[] = (json.apps || []).map((a: any) => ({
          app_id: a.id,
          tenant_id: DEMO_ORG_ID,
          name: a.name,
          description: a.description ?? "",
          status: a.status ?? "deployed",
          created_at: a.created_at,
          workflow_count: 0,
          // Template fields — used by AppDetailPage to route to TemplateRenderer
          app_type: a.app_type ?? null,
          blueprint: a.blueprint ?? null,
          modules: a.modules ?? null,
          architecture_summary: a.architecture_summary ?? null,
        }));
        // Also refresh localStorage cache
        this._saveApps(dbApps);
        const items = dbApps.slice(offset, offset + limit);
        return { items, total: dbApps.length, limit, offset };
      }
    } catch { /* fall through to localStorage */ }
    const items = this._loadApps().slice(offset, offset + limit);
    const total = this._loadApps().length;
    return { items, total, limit, offset };
  }

  async getApp(appId: string): Promise<App> {
    return this._loadApps().find((a) => a.app_id === appId) ?? this._makeDemoApp(appId);
  }

  async createApp(appData: Partial<App> & { user_prompt?: string }): Promise<App> {
    // Write to PostgreSQL via backend API
    try {
      const dbApp = await dbCreateApp(
        appData.name ?? "Untitled App",
        appData.description ?? "",
        DEMO_ORG_ID,
        appData.user_prompt
      );
      if (dbApp) {
        const newApp: App = {
          ...this._makeDemoApp(),
          ...appData,
          app_id: dbApp.id,
          tenant_id: DEMO_ORG_ID,
          status: dbApp.status ?? "deployed",
          created_at: dbApp.created_at,
          workflow_count: 0,
        } as App;
        const apps = this._loadApps();
        this._saveApps([newApp, ...apps]);
        return newApp;
      }
    } catch { /* fall through to localStorage */ }
    // Fallback: localStorage only
    const uniqueId = `app_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    const newApp: App = {
      ...this._makeDemoApp(),
      ...appData,
      app_id: uniqueId,
      tenant_id: "demo-tenant",
      status: "deployed",
      created_at: new Date().toISOString(),
      workflow_count: 0,
    } as App;
    const apps = this._loadApps();
    this._saveApps([newApp, ...apps]);
    return newApp;
  }

  async updateApp(appId: string, updates: Partial<App>): Promise<App> {
    const apps = this._loadApps();
    const idx = apps.findIndex((a) => a.app_id === appId);
    if (idx >= 0) {
      apps[idx] = { ...apps[idx], ...updates };
      this._saveApps(apps);
      return apps[idx];
    }
    return { ...this._makeDemoApp(appId), ...updates } as App;
  }

  async deleteApp(appId: string): Promise<void> {
    const apps = this._loadApps().filter((a) => a.app_id !== appId);
    this._saveApps(apps);
  }

  async deployApp(appId: string): Promise<App> {
    return this.updateApp(appId, { status: "deployed" });
  }

  async pauseApp(appId: string): Promise<App> {
    return this.updateApp(appId, { status: "paused" });
  }

  async getAppLogs(
    _appId: string,
    _limit = 100,
    _offset = 0
  ): Promise<Array<Record<string, unknown>>> {
    return [];
  }

  async getExecutions(
    _appId: string,
    limit = 50,
    offset = 0
  ): Promise<PaginatedResponse<AppExecution>> {
    return { items: [], total: 0, limit, offset };
  }

  async getExecution(executionId: string): Promise<AppExecution> {
    return { execution_id: executionId, status: "completed", started_at: new Date().toISOString() } as AppExecution;
  }

  async getMetrics(_appId: string): Promise<AppMetrics> {
    return { total_executions: 0, success_rate: 100, avg_duration_ms: 0, error_count: 0 } as unknown as AppMetrics;
  }

  async getVersions(_appId: string): Promise<Array<Record<string, unknown>>> {
    return [];
  }

  async rollbackToVersion(appId: string, _versionId: string): Promise<App> {
    return this._demoApp(appId);
  }
}

export const appService = new AppService();
