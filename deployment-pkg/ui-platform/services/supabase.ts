/**
 * Backend API client — SRP Autonomous OS
 *
 * Supabase has been removed. All database writes go through the
 * FastAPI backend at VITE_BACKEND_URL (default: http://localhost:8000).
 *
 * Endpoints used:
 *   POST  /api/records/apps       → create app row
 *   POST  /api/records/schemas    → save JSON schema
 *   POST  /api/records/data       → insert app_records row
 *   POST  /api/records/logs       → write execution_log
 */

const BACKEND_URL: string =
  (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "http://localhost:8000";

const DEMO_ORG_ID: string =
  (import.meta.env.VITE_DEMO_ORG_ID as string | undefined) ??
  "00000000-0000-0000-0000-000000000010";

// Always true — backend is always "configured" (it's local)
export const isSupabaseConfigured = (): boolean => true;

// ─── Types mirroring the foundation tables ───────────────────────────────────

export interface DbApp {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
}

export interface DbAppSchema {
  id: string;
  app_id: string;
  schema_json: Record<string, unknown>;
  version: number;
  created_at: string;
}

export interface DbAppRecord {
  id: string;
  app_id: string;
  record_json: Record<string, unknown>;
  created_at: string;
}

export interface DbExecutionLog {
  id: string;
  app_id: string | null;
  action: string;
  status: string;
  response_json: Record<string, unknown>;
  created_at: string;
}

// ─── Shared fetch helper ─────────────────────────────────────────────────────

async function apiPost<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── Typed helpers (same signatures as the old Supabase helpers) ─────────────

/**
 * Create a real app row in PostgreSQL.
 */
export async function dbCreateApp(
  name: string,
  description: string,
  organizationId: string = DEMO_ORG_ID,
  userPrompt?: string
): Promise<DbApp> {
  const result = await apiPost<{ ok: boolean; app: DbApp }>("/api/records/apps", {
    name,
    description,
    org_id: organizationId,
    ...(userPrompt ? { user_prompt: userPrompt } : {}),
  });
  return result.app;
}

/**
 * Store the planner JSON as an app_schema row.
 */
export async function dbSaveSchema(
  appId: string,
  schemaJson: Record<string, unknown>,
  version = 1,
  organizationId: string = DEMO_ORG_ID
): Promise<DbAppSchema> {
  const result = await apiPost<{ ok: boolean; schema: DbAppSchema }>("/api/records/schemas", {
    app_id: appId,
    schema_json: schemaJson,
    version,
    org_id: organizationId,
  });
  return result.schema;
}

/**
 * Insert a real data record into app_records.
 */
export async function dbInsertRecord(
  appId: string,
  recordJson: Record<string, unknown>,
  organizationId: string = DEMO_ORG_ID
): Promise<DbAppRecord> {
  const result = await apiPost<{ ok: boolean; record: DbAppRecord }>("/api/records/data", {
    app_id: appId,
    record_json: recordJson,
    org_id: organizationId,
  });
  return result.record;
}

/**
 * Fetch all rows from a whitelisted template table.
 */
export async function dbTableFetch(
  tableName: string,
  limit = 100
): Promise<{ columns: string[]; rows: Record<string, unknown>[] }> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/records/table/${tableName}?limit=${limit}`);
    if (!res.ok) return { columns: [], rows: [] };
    const json = await res.json();
    return { columns: json.columns ?? [], rows: json.rows ?? [] };
  } catch {
    return { columns: [], rows: [] };
  }
}

/**
 * Insert one row into a whitelisted template table.
 */
export async function dbTableInsert(
  tableName: string,
  row: Record<string, unknown>
): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/records/table/${tableName}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row }),
    });
    const json = await res.json();
    if (!res.ok) return { ok: false, error: json.detail ?? res.statusText };
    return { ok: true };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

/**
 * Fetch execution logs for an app from the backend.
 */
export async function dbGetExecutionLogs(
  appId: string,
  organizationId: string = DEMO_ORG_ID,
  limit = 50
): Promise<DbExecutionLog[]> {
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/records/logs/${appId}?org_id=${organizationId}&limit=${limit}`
    );
    if (!res.ok) return [];
    const json = await res.json();
    return (json.logs ?? []) as DbExecutionLog[];
  } catch {
    return [];
  }
}

/**
 * Write an immutable execution log entry.
 */
export async function dbLogExecution(
  appId: string,
  action: string,
  status: "success" | "error" | "pending",
  responseJson: Record<string, unknown> = {},
  organizationId: string = DEMO_ORG_ID
): Promise<DbExecutionLog> {
  const result = await apiPost<{ ok: boolean; log: DbExecutionLog }>("/api/records/logs", {
    app_id: appId,
    action,
    status,
    response: responseJson,
    org_id: organizationId,
  });
  return result.log;
}