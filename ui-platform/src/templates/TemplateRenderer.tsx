/**
 * TemplateRenderer
 *
 * Renders a fully dynamic UI driven by app.blueprint JSON.
 *
 * Blueprint schema
 * ─────────────────
 * {
 *   title?:          string
 *   description?:    string
 *   sidebar?: [
 *     { id, label, icon?, type: "crud"|"action"|"section", table?, action?,
 *       description?, endpoint? }
 *   ]
 *   summary_cards?: [
 *     { label, value?, icon?, color?: "blue"|"green"|"purple"|"orange"|"red"|"gray" }
 *   ]
 * }
 *
 * Routing:
 *   AppDetailPage → blueprint present → <TemplateRenderer blueprint={…} app={…} />
 *   AppDetailPage → no blueprint     → <GenericApp app={…} />
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MainLayout } from "../../components/layouts/MainLayout";
import { Card, Button } from "../../components/common/UIComponents";
import { ModuleCRUD } from "../../components/common/ModuleCRUD";
import { appService } from "../../services";
import { dbGetExecutionLogs, dbLogExecution } from "../../services/supabase";
import type { App } from "../../types";

const BACKEND_URL =
  (import.meta as { env?: Record<string, string> }).env?.VITE_BACKEND_URL ??
  "http://localhost:8000";

// ─── Blueprint type definitions ───────────────────────────────────────────────

export interface BlueprintSidebarItem {
  id: string;
  label: string;
  icon?: string;
  /** "crud" renders a ModuleCRUD panel; "action" renders a trigger button; "section" is a header-only divider */
  type: "crud" | "action" | "section";
  /** For type="crud": Supabase table name */
  table?: string;
  /** For type="action": logical action key (e.g. "generate_payroll") */
  action?: string;
  /** For type="action": optional backend endpoint to POST to */
  endpoint?: string;
  description?: string;
}

export interface BlueprintSummaryCard {
  label: string;
  value?: string | number;
  icon?: string;
  color?: "blue" | "green" | "purple" | "orange" | "red" | "gray";
}

export interface Blueprint {
  title?: string;
  description?: string;
  sidebar?: BlueprintSidebarItem[];
  summary_cards?: BlueprintSummaryCard[];
}

// ─── Enriched App type ────────────────────────────────────────────────────────

type RichApp = App & {
  app_type?: string | null;
  description?: string;
  blueprint?: Blueprint | string | null;
  [key: string]: unknown;
};

// ─── Constants ────────────────────────────────────────────────────────────────

const CARD_COLOR_MAP: Record<string, string> = {
  blue:   "text-blue-400",
  green:  "text-green-400",
  purple: "text-purple-400",
  orange: "text-orange-400",
  red:    "text-red-400",
  gray:   "text-gray-400",
};

// ─── Badge helpers ────────────────────────────────────────────────────────────

function statusBadge(status: string) {
  const map: Record<string, string> = {
    deployed: "bg-green-900 text-green-300 border-green-700",
    active:   "bg-green-900 text-green-300 border-green-700",
    paused:   "bg-yellow-900 text-yellow-300 border-yellow-700",
    draft:    "bg-gray-700 text-gray-300 border-gray-600",
    error:    "bg-red-900 text-red-300 border-red-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-semibold uppercase tracking-wide ${map[status] ?? "bg-gray-700 text-gray-300 border-gray-600"}`}>
      {status}
    </span>
  );
}

function appTypeBadge(appType?: string | null) {
  if (!appType || appType === "custom") return null;
  const colors: Record<string, string> = {
    payroll: "bg-blue-900 text-blue-300 border-blue-700",
    invoice: "bg-purple-900 text-purple-300 border-purple-700",
    crm:     "bg-orange-900 text-orange-300 border-orange-700",
  };
  const icons: Record<string, string> = { payroll: "💰", invoice: "📄", crm: "🤝" };
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-semibold uppercase tracking-wide ${colors[appType] ?? "bg-indigo-900 text-indigo-300 border-indigo-700"}`}>
      {icons[appType] ?? "⚙️"} {appType}
    </span>
  );
}

// ─── Action Module Panel ──────────────────────────────────────────────────────

interface ActionModuleProps {
  item: BlueprintSidebarItem;
  appId: string;
}

const ActionModule: React.FC<ActionModuleProps> = ({ item, appId }) => {
  const [running, setRunning]   = useState(false);
  const [result, setResult]     = useState<string | null>(null);
  const [isError, setIsError]   = useState(false);

  const handleAction = async () => {
    setRunning(true);
    setResult(null);
    setIsError(false);
    try {
      if (item.endpoint) {
        const res = await fetch(item.endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ app_id: appId }),
        });
        const data = await res.json();
        setResult(JSON.stringify(data, null, 2));
      } else {
        // Simulated execution — replace with real endpoint when available
        await new Promise<void>((r) => setTimeout(r, 1200));
        setResult(
          `✅ Action "${item.label}" executed successfully\n` +
          `   App ID : ${appId}\n` +
          `   Time   : ${new Date().toLocaleString()}`
        );
      }
      dbLogExecution(appId, item.action ?? item.id, "success", {}).catch(() => {});
    } catch (err) {
      setIsError(true);
      setResult(`❌ Error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="border border-gray-700 rounded-lg p-6 bg-gray-800/60">
        {item.description && (
          <p className="text-sm text-gray-400 mb-5 leading-relaxed">{item.description}</p>
        )}
        <Button onClick={handleAction} disabled={running} className="min-w-[180px]">
          {running ? "⏳ Running…" : `▶ ${item.label}`}
        </Button>
        {result && (
          <pre
            className={`mt-5 text-xs font-mono rounded p-4 whitespace-pre-wrap border ${
              isError
                ? "bg-red-950 border-red-800 text-red-300"
                : "bg-gray-950 border-gray-700 text-green-300"
            }`}
          >
            {result}
          </pre>
        )}
      </div>
    </div>
  );
};

// ─── Payroll Runs Module ──────────────────────────────────────────────────────

interface PayrollRunsModuleProps {
  appId: string;
  tableName: string;
  moduleLabel: string;
  onPayrollGenerated: (monthLabel: string) => void;
}

const PayrollRunsModule: React.FC<PayrollRunsModuleProps> = ({
  appId,
  tableName,
  moduleLabel,
  onPayrollGenerated,
}) => {
  const [generating, setGenerating] = useState(false);
  const [result, setResult]         = useState<string | null>(null);
  const [isError, setIsError]       = useState(false);
  const [tableKey, setTableKey]     = useState(0);

  const handleGenerate = async () => {
    setGenerating(true);
    setResult(null);
    setIsError(false);
    try {
      const res = await fetch(`${BACKEND_URL}/api/payroll/${appId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data: {
        ok?: boolean;
        message?: string;
        month_label?: string;
        detail?: string;
      } = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.detail ?? data.message ?? "Unknown error");
      }
      setResult(`✅ ${data.message}`);
      setTableKey((k) => k + 1); // force ModuleCRUD to re-fetch
      onPayrollGenerated(data.month_label ?? ""); // update summary card
      dbLogExecution(appId, "payroll_generate", "success", {
        month: data.month_label,
      }).catch(() => {});
    } catch (err) {
      setIsError(true);
      setResult(`❌ ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="border border-gray-700 rounded-lg p-4 bg-gray-800/60 flex flex-wrap items-center gap-3">
        <Button onClick={handleGenerate} disabled={generating} className="min-w-[200px]">
          {generating ? "⏳ Generating…" : "▶ Generate Payroll"}
        </Button>
        {result && (
          <span className={`text-sm font-mono ${isError ? "text-red-400" : "text-green-400"}`}>
            {result}
          </span>
        )}
      </div>
      <ModuleCRUD key={tableKey} tableName={tableName} moduleLabel={moduleLabel} />
    </div>
  );
};

// ─── Run History types ────────────────────────────────────────────────────────

interface BackendLog {
  id: string;
  action: string;
  status: string;
  created_at: string;
  response_json: Record<string, unknown>;
}

// ─── Main TemplateRenderer component ─────────────────────────────────────────

interface TemplateRendererProps {
  blueprint: Blueprint;
  app: RichApp;
}

export const TemplateRenderer: React.FC<TemplateRendererProps> = ({ blueprint, app }) => {
  const navigate  = useNavigate();

  // Sidebar selection
  const firstCrudOrAction = blueprint.sidebar?.find(
    (s) => s.type === "crud" || s.type === "action"
  );
  const [activeId, setActiveId] = useState<string>(
    firstCrudOrAction?.id ?? blueprint.sidebar?.[0]?.id ?? ""
  );

  // Rebuild
  const [rebuildInProgress, setRebuildInProgress] = useState(false);
  const [appState, setAppState] = useState<RichApp>(app);

  // Run history
  const [backendLogs, setBackendLogs]     = useState<BackendLog[]>([]);
  const [logsLoading, setLogsLoading]     = useState(false);

  // Summary card dynamic overrides (e.g. updated after payroll generation)
  const [summaryCardOverrides, setSummaryCardOverrides] = useState<Record<number, string>>({});

  useEffect(() => {
    let cancelled = false;
    const loadLogs = async () => {
      setLogsLoading(true);
      try {
        const logs = await dbGetExecutionLogs(app.app_id);
        if (!cancelled) setBackendLogs(logs as BackendLog[]);
      } catch { /* ignore */ }
      finally { if (!cancelled) setLogsLoading(false); }
    };
    loadLogs();
    return () => { cancelled = true; };
  }, [app.app_id]);

  const handlePayrollGenerated = (monthLabel: string) => {
    const idx = summaryCards.findIndex(
      (c) =>
        c.label.toLowerCase().includes("payroll run") ||
        c.label.toLowerCase().includes("last payroll"),
    );
    if (idx >= 0) {
      setSummaryCardOverrides((prev) => ({ ...prev, [idx]: monthLabel }));
    }
  };

  const handleRebuild = async () => {
    setRebuildInProgress(true);
    try {
      const updated = await appService.deployApp(appState.app_id);
      setAppState(updated as RichApp);
      dbLogExecution(appState.app_id, "app_rebuild", "success", { name: appState.name }).catch(() => {});
    } finally {
      setRebuildInProgress(false);
    }
  };

  const activeItem = blueprint.sidebar?.find((s) => s.id === activeId);
  const summaryCards: BlueprintSummaryCard[] = blueprint.summary_cards ?? [];

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <MainLayout>
      <div className="space-y-6 pb-16">

        {/* ── HEADER ────────────────────────────────────────────────────── */}
        <div>
          <nav className="text-sm text-gray-500 mb-3">
            <button
              onClick={() => navigate("/apps")}
              className="hover:text-white transition-colors"
            >
              ← Applications
            </button>
            <span className="mx-2 text-gray-700">/</span>
            <span className="text-gray-300">{appState.name}</span>
          </nav>

          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold text-white">{appState.name}</h1>
                {statusBadge(appState.status)}
                {appTypeBadge(appState.app_type)}
              </div>
              {appState.description && (
                <p className="text-gray-400 max-w-2xl text-sm leading-relaxed">
                  {appState.description}
                </p>
              )}
              <p className="text-gray-600 text-xs mt-1 font-mono">{appState.app_id}</p>
            </div>

            <div className="flex flex-wrap gap-2 shrink-0">
              <Button
                variant="secondary"
                onClick={handleRebuild}
                disabled={rebuildInProgress}
              >
                {rebuildInProgress ? "⏳ Rebuilding…" : "🔁 Rebuild"}
              </Button>
              {appState.status === "deployed" ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={async () =>
                    setAppState((await appService.pauseApp(appState.app_id)) as RichApp)
                  }
                >
                  ⏸ Pause
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={async () =>
                    setAppState((await appService.deployApp(appState.app_id)) as RichApp)
                  }
                >
                  ▶ Deploy
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* ── SUMMARY CARDS ─────────────────────────────────────────────── */}
        {summaryCards.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {summaryCards.map((card, i) => (
              <Card key={i}>
                <div className="flex items-center gap-2 mb-1">
                  {card.icon && <span className="text-lg">{card.icon}</span>}
                  <p className="text-xs text-gray-500">{card.label}</p>
                </div>
                <p className={`text-2xl font-bold ${CARD_COLOR_MAP[card.color ?? "gray"]}`}>
                  {summaryCardOverrides[i] ?? card.value ?? "—"}
                </p>
              </Card>
            ))}
          </div>
        )}

        {/* ── MAIN CONTENT: Sidebar + Panel ─────────────────────────────── */}
        {blueprint.sidebar && blueprint.sidebar.length > 0 && (
          <div className="flex gap-5">

            {/* ── Sidebar navigation ──────────────────────────────────── */}
            <aside className="w-56 shrink-0">
              <nav className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
                {blueprint.sidebar.map((item) => {
                  if (item.type === "section") {
                    return (
                      <div
                        key={item.id}
                        className="px-4 pt-4 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider"
                      >
                        {item.label}
                      </div>
                    );
                  }
                  const isActive = activeId === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveId(item.id)}
                      className={`w-full flex items-center gap-2.5 px-4 py-3 text-sm text-left transition-colors ${
                        isActive
                          ? "bg-blue-900/50 text-white border-l-2 border-blue-500"
                          : "text-gray-400 hover:text-white hover:bg-gray-700/50 border-l-2 border-transparent"
                      }`}
                    >
                      {item.icon && <span className="text-base">{item.icon}</span>}
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </aside>

            {/* ── Content panel ───────────────────────────────────────── */}
            <div className="flex-1 min-w-0">
              {activeItem ? (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    {activeItem.icon && <span className="text-lg">{activeItem.icon}</span>}
                    <h2 className="text-base font-semibold text-white">{activeItem.label}</h2>
                    <span className="text-xs bg-gray-700 text-gray-400 border border-gray-600 rounded px-2 py-0.5 uppercase">
                      {activeItem.type}
                    </span>
                  </div>

                  {activeItem.type === "crud" && activeItem.table ? (
                    activeItem.id === "payroll_run_engine" ? (
                      <PayrollRunsModule
                        key={activeItem.id}
                        appId={app.app_id}
                        tableName={activeItem.table}
                        moduleLabel={activeItem.label}
                        onPayrollGenerated={handlePayrollGenerated}
                      />
                    ) : (
                      <ModuleCRUD
                        key={activeItem.id}
                        tableName={activeItem.table}
                        moduleLabel={activeItem.label}
                      />
                    )
                  ) : activeItem.type === "action" ? (
                    <ActionModule key={activeItem.id} item={activeItem} appId={app.app_id} />
                  ) : (
                    <Card>
                      <p className="text-gray-500 text-sm">
                        {activeItem.description ?? "No content configured for this item."}
                      </p>
                    </Card>
                  )}
                </div>
              ) : (
                <Card>
                  <p className="text-gray-500 text-sm text-center py-8">
                    Select an item from the sidebar.
                  </p>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* ── RUN HISTORY (global — always visible) ─────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Run History
            </h2>
            <div className="flex items-center gap-3">
              {logsLoading && (
                <span className="text-xs text-gray-500 animate-pulse">
                  Loading backend logs…
                </span>
              )}
              <span className="text-xs text-gray-600">
                {backendLogs.length} backend entries
              </span>
            </div>
          </div>

          {backendLogs.length === 0 ? (
            <Card>
              <p className="text-gray-500 text-sm text-center py-8">
                No executions logged yet — trigger an action to see history here.
              </p>
            </Card>
          ) : (
            <div className="space-y-2">
              {backendLogs.map((log) => (
                <div
                  key={log.id}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 flex items-center gap-3 text-sm"
                >
                  <span className={log.status === "success" ? "text-green-400" : "text-yellow-400"}>
                    {log.status === "success" ? "✅" : "⚠️"}
                  </span>
                  <span className="text-gray-300 flex-1 font-mono text-xs">{log.action}</span>
                  <span className="text-gray-500 text-xs">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      log.status === "success"
                        ? "bg-green-900 text-green-300"
                        : "bg-yellow-900 text-yellow-300"
                    }`}
                  >
                    {log.status.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

      </div>
    </MainLayout>
  );
};

export default TemplateRenderer;
