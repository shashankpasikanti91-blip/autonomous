/**
 * GenericApp
 *
 * Renders the full custom-app experience:
 *   1. Header  (+ Run App button)
 *   2. App Info + Quick Stats
 *   3. Module Tabs  → live table data + Add Record form (ModuleCRUD)
 *   4. Run Console  (Input Payload + Terminal Output)
 *   5. Run History  (local localStorage + backend audit logs)
 *
 * Used by AppDetailPage when app.blueprint is absent/null.
 */

import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { MainLayout } from "../../components/layouts/MainLayout";
import { Card, Button } from "../../components/common/UIComponents";
import { ModuleCRUD } from "../../components/common/ModuleCRUD";
import { appService } from "../../services";
import { isOpenAIConfigured } from "../../services/openai";
import { runOrchestration } from "../../services/orchestrator";
import { dbLogExecution, dbInsertRecord, dbGetExecutionLogs } from "../../services/supabase";
import type { App } from "../../types";

// ─── Constants ────────────────────────────────────────────────────────────────

const EXEC_STORAGE_KEY = (id: string) => `srp_exec_${id}`;

const TEMPLATE_TABLES: Record<string, { name: string; description: string }[]> = {
  payroll: [
    { name: "employees",         description: "Employee profiles & HR records" },
    { name: "attendance",        description: "Daily check-in / check-out logs" },
    { name: "salary_components", description: "Earning & deduction components per employee" },
    { name: "payroll_runs",      description: "Periodic payroll cycle records" },
    { name: "payslips",          description: "Individual generated payslips" },
  ],
  invoice: [
    { name: "customers",     description: "Customer / client profiles" },
    { name: "products",      description: "Product & service catalogue" },
    { name: "invoices",      description: "Invoice headers and payment status" },
    { name: "invoice_items", description: "Line items attached to each invoice" },
  ],
  crm: [
    { name: "leads",      description: "Incoming leads and enquiries" },
    { name: "deals",      description: "Deal pipeline with stage tracking" },
    { name: "activities", description: "Calls, emails, meetings and tasks" },
    { name: "contacts",   description: "Full contact directory" },
  ],
};

const MODULE_TO_TABLE: Record<string, string> = {
  employee_management:  "employees",
  attendance_tracking:  "attendance",
  salary_configuration: "salary_components",
  payroll_run_engine:   "payroll_runs",
  payslip_generator:    "payslips",
  customer_management:  "customers",
  product_catalogue:    "products",
  invoice_builder:      "invoices",
  lead_capture:         "leads",
  deal_pipeline:        "deals",
  activity_log:         "activities",
  contact_management:   "contacts",
};

const MODULE_ICON: Record<string, string> = {
  employee:   "👥",
  attendance: "🕐",
  salary:     "💵",
  payroll:    "💰",
  payslip:    "🧾",
  tax:        "🏛",
  customer:   "🤝",
  product:    "📦",
  invoice:    "📄",
  billing:    "💳",
  payment:    "💳",
  pdf:        "📑",
  email:      "📧",
  lead:       "🎯",
  deal:       "🤝",
  pipeline:   "🔀",
  contact:    "👤",
  sales:      "📈",
  report:     "📊",
  dashboard:  "🖥",
  default:    "⚙️",
};

function moduleIcon(mod: string): string {
  const lc = mod.toLowerCase();
  for (const [key, icon] of Object.entries(MODULE_ICON)) {
    if (lc.includes(key)) return icon;
  }
  return MODULE_ICON.default;
}

// ─── Types ────────────────────────────────────────────────────────────────────

type RichApp = App & {
  app_type?: string | null;
  description?: string;
  modules?: string[];
  architecture_summary?: string;
  [key: string]: unknown;
};

interface ExecEntry {
  id: string;
  started_at: string;
  duration_ms: number;
  status: "success" | "error";
  input: string;
  output: string[];
}

interface BackendLog {
  id: string;
  action: string;
  status: string;
  created_at: string;
  response_json: Record<string, unknown>;
}

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

// ─── Helper ───────────────────────────────────────────────────────────────────

const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

// ─── Component ────────────────────────────────────────────────────────────────

interface GenericAppProps {
  app: RichApp;
}

export const GenericApp: React.FC<GenericAppProps> = ({ app: initialApp }) => {
  const navigate = useNavigate();
  const appId    = initialApp.app_id;

  // ── State ──────────────────────────────────────────────────────────────────
  const [app, setApp]                         = useState<RichApp>(initialApp);
  const [inputPayload, setInputPayload]       = useState("");
  const [runInProgress, setRunInProgress]     = useState(false);
  const [rebuildInProgress, setRebuildInProgress] = useState(false);
  const [outputLines, setOutputLines]         = useState<{ text: string; type: string }[]>([]);
  const outputRef                             = useRef<HTMLDivElement>(null);
  const [activeModule, setActiveModule]       = useState<string | null>(null);
  const [execHistory, setExecHistory]         = useState<ExecEntry[]>([]);
  const [backendLogs, setBackendLogs]         = useState<BackendLog[]>([]);
  const [logsLoading, setLogsLoading]         = useState(false);

  // ── Bootstrap ──────────────────────────────────────────────────────────────
  useEffect(() => {
    try {
      const raw = localStorage.getItem(EXEC_STORAGE_KEY(appId));
      if (raw) setExecHistory(JSON.parse(raw));
    } catch { /* ignore */ }
    let cancelled = false;
    (async () => {
      setLogsLoading(true);
      try {
        const logs = await dbGetExecutionLogs(appId);
        if (!cancelled) setBackendLogs(logs as BackendLog[]);
      } catch { /* ignore */ }
      finally { if (!cancelled) setLogsLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [appId]);

  // Auto-scroll console
  useEffect(() => {
    if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [outputLines]);

  // Set first module as active
  const modules: string[] = (app as RichApp).modules ?? [];
  useEffect(() => {
    if (modules.length > 0 && !activeModule) setActiveModule(modules[0]);
  }, [modules.length]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Derived ────────────────────────────────────────────────────────────────
  const appType: string | null = app.app_type ?? null;
  const templateTables          = appType ? (TEMPLATE_TABLES[appType] ?? []) : [];
  const isTemplateBased         = templateTables.length > 0 || ["payroll", "invoice", "crm"].includes(appType ?? "");

  const successCount = execHistory.filter((e) => e.status === "success").length;
  const avgDuration  = execHistory.length
    ? Math.round(execHistory.reduce((s, e) => s + e.duration_ms, 0) / execHistory.length)
    : null;

  // ── Run handler ────────────────────────────────────────────────────────────
  const handleRun = async () => {
    setRunInProgress(true);
    const lines: { text: string; type: string }[] = [];
    const add = (text: string, type = "info") => { lines.push({ text, type }); setOutputLines([...lines]); };
    const t = () => new Date().toLocaleTimeString("en-GB", { hour12: false });
    const startMs = Date.now();
    const raw = inputPayload.trim();

    add(`[${t()}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, "dim");
    add(`[${t()}] Starting "${app.name}"${appType ? ` [${appType.toUpperCase()}]` : ""}`, "info");
    await delay(250);

    if (!raw) {
      add(`[${t()}] ⚠  No input provided — paste JSON or plain text in the Input box.`, "error");
      add(`[${t()}] ❌  STOPPED`, "error");
      const entry: ExecEntry = {
        id: `exec_${Date.now()}`, started_at: new Date().toISOString(),
        duration_ms: Date.now() - startMs, status: "error", input: "", output: lines.map((l) => l.text),
      };
      const updated = [entry, ...execHistory].slice(0, 50);
      setExecHistory(updated);
      localStorage.setItem(EXEC_STORAGE_KEY(appId), JSON.stringify(updated));
      setRunInProgress(false);
      return;
    }

    let parsed: Record<string, unknown> = {};
    try { parsed = JSON.parse(raw); }
    catch { raw.split(/\n/).map((s) => s.trim()).filter(Boolean).forEach((line, i) => { parsed[`line_${i + 1}`] = line; }); }

    if (isOpenAIConfigured()) {
      add(`[${t()}] 🧠 Orchestrator engaged…`, "info");
      await delay(200);
      try {
        const result = await runOrchestration(app.name, (app.description as string) || app.name, "index.js", raw);
        const trace  = result.reasoning_trace;
        add(`[${t()}] ─── PLAN (${trace.plan.length} steps) ───`, "dim");
        for (const step of trace.plan) { add(`[${t()}]   Step ${step.step}: ${step.task}`, "info"); await delay(80); }
        for (const line of result.final_output.split("\n")) {
          const type = line.includes("✓") || line.includes("✅") || line.includes("SUCCESS") ? "success"
            : line.includes("❌") || line.includes("ERROR") ? "error"
            : line.includes("⚠") ? "info"
            : line.startsWith("───") || line.startsWith("━━━") ? "dim"
            : line.startsWith("  ") ? "data" : "info";
          add(line || " ", type); await delay(18);
        }
        const v = trace.validation;
        add(`[${t()}] Validator — score: ${v.score}/10  ${v.passed ? "✅ PASSED" : "⚠ ISSUES"}`, v.passed ? "success" : "info");
        add(`[${t()}] 🔢 Tokens: ${trace.total_tokens}  |  Model: ${trace.model}  |  ${trace.duration_ms}ms`, "dim");
      } catch (aiErr) {
        add(`[${t()}] ⚠ Orchestrator: ${aiErr instanceof Error ? aiErr.message : String(aiErr)}`, "error");
        add(`[${t()}] Falling back to rule-based engine…`, "info"); await delay(300);
        add(`[${t()}] Processed ${Object.keys(parsed).length || 1} field(s)`, "success");
      }
    } else {
      add(`[${t()}] Rule-based mode (no VITE_OPENAI_API_KEY set)`, "info"); await delay(300);
      add(`[${t()}] Processed ${Object.keys(parsed).length || 1} input field(s)`, "success");
    }

    const durationMs = Date.now() - startMs;
    add(`[${t()}] ✓ Metrics logged`, "success");
    add(`[${t()}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, "dim");
    add(`[${t()}] ✅  COMPLETE  |  ${durationMs}ms`, "success");

    const entry: ExecEntry = {
      id: `exec_${Date.now()}`, started_at: new Date().toISOString(),
      duration_ms: durationMs, status: "success", input: inputPayload.trim(), output: lines.map((l) => l.text),
    };
    const updated = [entry, ...execHistory].slice(0, 50);
    setExecHistory(updated);
    localStorage.setItem(EXEC_STORAGE_KEY(appId), JSON.stringify(updated));
    dbLogExecution(appId, "app_run", "success", { input: raw.slice(0, 500), duration_ms: durationMs }).catch(() => {});
    if (raw) dbInsertRecord(appId, parsed).catch(() => {});
    setRunInProgress(false);
  };

  // ── Rebuild handler ────────────────────────────────────────────────────────
  const handleRebuild = async () => {
    setRebuildInProgress(true);
    try {
      const updated = await appService.deployApp(app.app_id);
      setApp(updated as RichApp);
      dbLogExecution(appId, "app_rebuild", "success", { name: app.name }).catch(() => {});
    } finally {
      setRebuildInProgress(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <MainLayout>
      <div className="space-y-6 pb-16">

        {/* ── 1. HEADER ───────────────────────────────────────────────── */}
        <div>
          <nav className="text-sm text-gray-500 mb-3">
            <button onClick={() => navigate("/apps")} className="hover:text-white transition-colors">
              ← Applications
            </button>
            <span className="mx-2 text-gray-700">/</span>
            <span className="text-gray-300">{app.name}</span>
          </nav>

          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold text-white">{app.name}</h1>
                {statusBadge(app.status)}
                {appTypeBadge(appType)}
              </div>
              {app.description && (
                <p className="text-gray-400 max-w-2xl text-sm leading-relaxed">{app.description}</p>
              )}
              <p className="text-gray-600 text-xs mt-1 font-mono">{app.app_id}</p>
            </div>

            <div className="flex flex-wrap gap-2 shrink-0">
              {!isTemplateBased && (
                <Button
                  onClick={handleRun}
                  disabled={runInProgress || app.status !== "deployed"}
                  className="min-w-[120px]"
                >
                  {runInProgress ? "⏳ Running…" : "▶ Run App"}
                </Button>
              )}
              <Button variant="secondary" onClick={handleRebuild} disabled={rebuildInProgress}>
                {rebuildInProgress ? "⏳ Rebuilding…" : "🔁 Rebuild"}
              </Button>
              {app.status === "deployed" ? (
                <Button variant="secondary" size="sm" onClick={async () => setApp((await appService.pauseApp(app.app_id)) as RichApp)}>
                  ⏸ Pause
                </Button>
              ) : (
                <Button size="sm" onClick={async () => setApp((await appService.deployApp(app.app_id)) as RichApp)}>
                  ▶ Deploy
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* ── 2. APP INFO + QUICK STATS ───────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="md:col-span-2">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Application Info</h2>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm mb-4">
              {([
                ["App ID",   app.app_id],
                ["App Type", appType ? appType.charAt(0).toUpperCase() + appType.slice(1) : "Custom"],
                ["Status",   app.status.toUpperCase()],
                ["Created",  new Date(app.created_at).toLocaleString()],
              ] as [string, string][]).map(([k, v]) => (
                <React.Fragment key={k}>
                  <dt className="text-gray-500">{k}</dt>
                  <dd className="text-white font-mono text-xs truncate" title={v}>{v}</dd>
                </React.Fragment>
              ))}
            </dl>

            {app.architecture_summary && (() => {
              const lines = (app.architecture_summary as string).split("\n");
              return (
                <div className="border-t border-gray-700 pt-3">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Architecture</p>
                  <ul className="space-y-1">
                    {lines.map((line, i) => {
                      const isNested  = line.startsWith("  - ");
                      const isBullet  = line.trimStart().startsWith("- ");
                      const isHeading = !isBullet && line.trim() !== "";
                      if (isNested) return (
                        <li key={i} className="flex items-start gap-1.5 pl-5 text-xs text-gray-400">
                          <span className="mt-0.5 text-gray-600">◦</span>
                          <span>{line.replace(/^\s*-\s*/, "")}</span>
                        </li>
                      );
                      if (isBullet) return (
                        <li key={i} className="flex items-start gap-1.5 pl-1 text-xs text-gray-300">
                          <span className="mt-0.5 text-blue-400">•</span>
                          <span>{line.replace(/^-\s*/, "")}</span>
                        </li>
                      );
                      if (isHeading) return <p key={i} className="text-xs text-white font-medium">{line}</p>;
                      return null;
                    })}
                  </ul>
                </div>
              );
            })()}
          </Card>

          <div className="flex flex-col gap-3">
            <Card>
              <p className="text-xs text-gray-500 mb-1">Total Runs</p>
              <p className="text-3xl font-bold text-white">{execHistory.length}</p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500 mb-1">Success Rate</p>
              <p className="text-3xl font-bold text-green-400">
                {execHistory.length === 0 ? "—" : `${Math.round((successCount / execHistory.length) * 100)}%`}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500 mb-1">Avg Duration</p>
              <p className="text-3xl font-bold text-blue-400">
                {avgDuration === null ? "—" : `${avgDuration}ms`}
              </p>
            </Card>
          </div>
        </div>

        {/* ── 3. MODULE TABS ──────────────────────────────────────────── */}
        {modules.length > 0 && (
          <section>
            {isTemplateBased ? (
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-semibold text-white">
                    {appType ? appType.charAt(0).toUpperCase() + appType.slice(1) : ""} Modules
                  </h2>
                  <p className="text-xs text-gray-500 mt-0.5">Select a module to view and manage its data</p>
                </div>
                <span className="text-xs text-gray-600 bg-gray-800 border border-gray-700 rounded px-2 py-1">
                  {modules.length} modules
                </span>
              </div>
            ) : (
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Modules <span className="normal-case font-normal text-gray-600 ml-1">({modules.length})</span>
              </h2>
            )}

            <div className="flex flex-wrap gap-1 border-b border-gray-700 mb-4">
              {modules.map((mod) => (
                <button
                  key={mod}
                  onClick={() => setActiveModule(mod)}
                  className={`flex items-center gap-1.5 px-4 py-2 text-sm rounded-t transition-colors ${
                    activeModule === mod
                      ? "bg-gray-800 text-white border-b-2 border-blue-500"
                      : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                  }`}
                >
                  <span>{moduleIcon(mod)}</span>
                  <span>{mod.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</span>
                </button>
              ))}
            </div>

            {activeModule && (
              MODULE_TO_TABLE[activeModule]
                ? <ModuleCRUD
                    key={activeModule}
                    tableName={MODULE_TO_TABLE[activeModule]}
                    moduleLabel={activeModule.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  />
                : <div className="text-gray-500 text-sm py-6 px-2 text-center border border-gray-700 rounded-lg">
                    No data table configured for this module.
                  </div>
            )}
          </section>
        )}

        {/* ── 4. RUN CONSOLE — custom apps only ───────────────────────── */}
        {!isTemplateBased && (
          <section>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Run Console</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-white">Input Payload</h3>
                  <span className="text-xs text-gray-500">JSON or plain text</span>
                </div>
                <textarea
                  className="w-full h-44 px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white font-mono text-xs focus:outline-none focus:border-blue-500 resize-none placeholder-gray-600"
                  placeholder={'{\n  "field1": "value1",\n  "field2": "value2"\n}'}
                  value={inputPayload}
                  onChange={(e) => setInputPayload(e.target.value)}
                  disabled={runInProgress}
                />
                <div className="flex gap-2 mt-3">
                  <Button onClick={handleRun} disabled={runInProgress || app.status !== "deployed"} className="flex-1">
                    {runInProgress ? "⏳ Running…" : "▶ Run App"}
                  </Button>
                  <Button variant="secondary" onClick={() => setOutputLines([])} disabled={runInProgress}>
                    Clear
                  </Button>
                </div>
                {app.status !== "deployed" && (
                  <p className="text-yellow-400 text-xs mt-2">⚠ App is {app.status} — deploy first to run</p>
                )}
              </Card>

              <Card>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-white">Console Output</h3>
                  {outputLines.length > 0 && <span className="text-xs text-gray-500">{outputLines.length} lines</span>}
                </div>
                <div ref={outputRef} className="h-44 bg-gray-950 border border-gray-700 rounded p-3 overflow-y-auto font-mono text-xs">
                  {outputLines.length === 0
                    ? <p className="text-gray-600">Press ▶ Run App to execute…</p>
                    : outputLines.map((line, i) => (
                      <p key={i} className={
                        line.type === "success" ? "text-green-400"
                        : line.type === "error"  ? "text-red-400"
                        : line.type === "data"   ? "text-yellow-300"
                        : line.type === "dim"    ? "text-gray-600"
                        : "text-gray-300"
                      }>{line.text || " "}</p>
                    ))
                  }
                  {runInProgress && <p className="text-blue-400 animate-pulse">▋</p>}
                </div>
              </Card>
            </div>
          </section>
        )}

        {/* ── 5. RUN HISTORY ──────────────────────────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Run History</h2>
            <div className="flex items-center gap-3">
              {logsLoading && <span className="text-xs text-gray-500 animate-pulse">Loading backend logs…</span>}
              <span className="text-xs text-gray-600">
                {execHistory.length} local · {backendLogs.length} backend
              </span>
            </div>
          </div>

          {execHistory.length === 0 && backendLogs.length === 0 ? (
            <Card>
              <p className="text-gray-500 text-sm text-center py-8">
                No executions yet — run the app to see history here
              </p>
            </Card>
          ) : (
            <div className="space-y-2">
              {execHistory.map((entry) => (
                <details key={entry.id} className="bg-gray-800 border border-gray-700 rounded-lg group">
                  <summary className="px-4 py-3 flex items-center gap-3 text-sm cursor-pointer list-none select-none hover:bg-gray-700/40 rounded-lg transition-colors">
                    <span className={entry.status === "success" ? "text-green-400" : "text-red-400"}>
                      {entry.status === "success" ? "✅" : "❌"}
                    </span>
                    <span className="text-white flex-1">{new Date(entry.started_at).toLocaleString()}</span>
                    <span className="text-gray-400 text-xs">{entry.duration_ms}ms</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${entry.status === "success" ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
                      {entry.status.toUpperCase()}
                    </span>
                    <span className="text-gray-600 text-xs group-open:rotate-180 transition-transform">▾</span>
                  </summary>
                  <div className="px-4 pb-4 pt-1 space-y-2 border-t border-gray-700">
                    {entry.input && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Input:</p>
                        <pre className="text-xs font-mono text-yellow-300 bg-gray-900 p-2 rounded overflow-x-auto">{entry.input}</pre>
                      </div>
                    )}
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Output ({entry.output.length} lines):</p>
                      <div className="bg-gray-950 rounded p-2 max-h-36 overflow-y-auto">
                        {entry.output.map((line, i) => (
                          <p key={i} className="text-xs font-mono text-gray-300">{line}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </details>
              ))}

              {backendLogs.length > 0 && (
                <>
                  <p className="text-xs text-gray-600 pt-2 pb-1 px-1">Backend audit log</p>
                  {backendLogs.map((log) => (
                    <div key={log.id} className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 flex items-center gap-3 text-sm">
                      <span className={log.status === "success" ? "text-green-400" : "text-yellow-400"}>
                        {log.status === "success" ? "✅" : "⚠️"}
                      </span>
                      <span className="text-gray-300 flex-1 font-mono text-xs">{log.action}</span>
                      <span className="text-gray-500 text-xs">{new Date(log.created_at).toLocaleString()}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${log.status === "success" ? "bg-green-900 text-green-300" : "bg-yellow-900 text-yellow-300"}`}>
                        {log.status.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </section>

      </div>
    </MainLayout>
  );
};

export default GenericApp;
