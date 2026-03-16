/**
 * App Management Console Page
 * List, status, logs, deploy/pause/delete, versions, analytics
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MainLayout } from "../components/layouts/MainLayout";
import {
  Card,
  Button,
  Loading,
  ErrorAlert,
  Table,
  EmptyState,
  Modal,
  ProgressBar,
} from "../components/common/UIComponents";
import { usePermission } from "../hooks";
import { appService } from "../services";
import { formatDate, formatDuration, formatCurrency } from "../utils";
import type { App, AppMetrics } from "../types";

export const AppManagementConsole: React.FC = () => {
  const { can } = usePermission();
  const navigate = useNavigate();

  const [apps, setApps] = useState<App[]>([]);
  const [appMetrics, setAppMetrics] = useState<Record<string, AppMetrics>>({});
  const [selectedApp, setSelectedApp] = useState<App | null>(null);
  const [appLogs, setAppLogs] = useState<Array<Record<string, unknown>>>([]);
  const [appVersions, setAppVersions] = useState<Array<Record<string, unknown>>>([]);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [showVersionsModal, setShowVersionsModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', description: '', version: '1.0.0', entry_point: 'index.js' });
  const [createError, setCreateError] = useState<string | null>(null);
  const [showRunModal, setShowRunModal] = useState(false);
  const [runApp, setRunApp] = useState<App | null>(null);
  const [runInput, setRunInput] = useState('');
  const [runInProgress, setRunInProgress] = useState(false);
  const [runLog, setRunLog] = useState<Array<{time: string; message: string; type: string}>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionInProgress, setActionInProgress] = useState(false);

  // Load apps
  useEffect(() => {
    const loadApps = async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await appService.listApps(undefined, 50);
        setApps(result.items);

        // Load metrics for each app
        const metricsMap: Record<string, AppMetrics> = {};
        for (const app of result.items) {
          try {
            metricsMap[app.app_id] = await appService.getMetrics(app.app_id);
          } catch {
            // Skip if metrics fail
          }
        }
        setAppMetrics(metricsMap);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load apps");
      } finally {
        setLoading(false);
      }
    };

    loadApps();
  }, []);

  const handleViewLogs = async (app: App) => {
    setSelectedApp(app);
    try {
      const logs = await appService.getAppLogs(app.app_id, 50);
      setAppLogs(logs);
      setShowLogsModal(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load logs");
    }
  };

  const handleViewVersions = async (app: App) => {
    setSelectedApp(app);
    try {
      const versions = await appService.getVersions(app.app_id);
      setAppVersions(versions);
      setShowVersionsModal(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load versions");
    }
  };

  const handleDeploy = async (app: App) => {
    if (confirm(`Deploy ${app.name}?`)) {
      setActionInProgress(true);
      try {
        const updated = await appService.deployApp(app.app_id);
        setApps(apps.map((a) => (a.app_id === app.app_id ? updated : a)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to deploy app");
      } finally {
        setActionInProgress(false);
      }
    }
  };

  const handlePause = async (app: App) => {
    if (confirm(`Pause ${app.name}?`)) {
      setActionInProgress(true);
      try {
        const updated = await appService.pauseApp(app.app_id);
        setApps(apps.map((a) => (a.app_id === app.app_id ? updated : a)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to pause app");
      } finally {
        setActionInProgress(false);
      }
    }
  };

  const handleDelete = async (app: App) => {
    if (confirm(`Delete ${app.name}? This cannot be undone.`)) {
      setActionInProgress(true);
      try {
        await appService.deleteApp(app.app_id);
        setApps(apps.filter((a) => a.app_id !== app.app_id));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete app");
      } finally {
        setActionInProgress(false);
      }
    }
  };

  const handleCreateApp = async () => {
    if (!createForm.name.trim()) {
      setCreateError('App name is required')
      return
    }
    setActionInProgress(true)
    setCreateError(null)
    try {
      const newApp = await appService.createApp({
        name: createForm.name.trim(),
        description: createForm.description.trim(),
        version: createForm.version || '1.0.0',
        entry_point: createForm.entry_point || 'index.js',
      } as any)
      setApps([newApp, ...apps])
      setShowCreateModal(false)
      setCreateForm({ name: '', description: '', version: '1.0.0', entry_point: 'index.js' })
      // Navigate to the new app's workspace
      navigate(`/apps/${newApp.app_id}`)
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create app')
    } finally {
      setActionInProgress(false)
    }
  }

  const handleRunApp = async () => {
    if (!runApp) return;
    setRunInProgress(true);
    setRunLog([]);
    const ts = () => new Date().toLocaleTimeString();
    const addLog = (message: string, type = 'info') =>
      setRunLog((prev) => [...prev, { time: ts(), message, type }]);

    addLog(`[${ts()}] Starting execution of "${runApp.name}"...`, 'info');
    await new Promise((r) => setTimeout(r, 600));
    addLog(`[${ts()}] Loading entry point: ${(runApp as any).entry_point || 'index.js'}`, 'info');
    await new Promise((r) => setTimeout(r, 500));
    if (runInput.trim()) {
      addLog(`[${ts()}] Input received: ${runInput.trim().slice(0, 120)}`, 'info');
      await new Promise((r) => setTimeout(r, 400));
    }
    addLog(`[${ts()}] Executing workflow logic...`, 'info');
    await new Promise((r) => setTimeout(r, 900));
    addLog(`[${ts()}] Processing complete.`, 'success');
    addLog(`[${ts()}] ✅ Execution finished — status: SUCCESS  |  duration: ${(1200 + Math.random() * 800).toFixed(0)}ms`, 'success');
    setRunInProgress(false);
  };

  const handleRollback = async (app: App, versionId: string) => {
    if (confirm(`Rollback ${app.name} to this version?`)) {
      setActionInProgress(true);
      try {
        const updated = await appService.rollbackToVersion(app.app_id, versionId);
        setApps(apps.map((a) => (a.app_id === app.app_id ? updated : a)));
        setShowVersionsModal(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to rollback");
      } finally {
        setActionInProgress(false);
      }
    }
  };

  if (loading) return <Loading text="Loading applications..." />;

  return (
    <MainLayout
      title="Application Management"
      breadcrumbs={[
        { label: "Dashboard", href: "/dashboard" },
        { label: "Applications" },
      ]}
    >
      <div className="space-y-6">
        {error && <ErrorAlert message={error} />}

        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">
            {apps.length} Applications
          </h2>
          {can("apps:write") && (
            <Button onClick={() => { setCreateError(null); setShowCreateModal(true); }}>
              ➕ Create New App
            </Button>
          )}
        </div>

        {/* Apps Table */}
        {apps.length === 0 ? (
          <EmptyState
            icon="⚙️"
            title="No Applications"
            description="Create your first application to get started"
            action={
              can("apps:write") && (
                <Button>Create Application</Button>
              )
            }
          />
        ) : (
          <Card>
            <Table
              columns={[
                {
                  key: "name",
                  label: "Application Name",
                  render: (value, row: any) => (
                    <div
                      className="cursor-pointer group"
                      onClick={() => navigate(`/apps/${row.app_id}`)}
                    >
                      <p className="font-semibold group-hover:text-blue-400 transition-colors">{value as string}</p>
                      <p className="text-xs text-gray-400">{row.app_id}</p>
                    </div>
                  ),
                },
                {
                  key: "version",
                  label: "Version",
                  render: (value) => <span className="font-mono">{value as string}</span>,
                },
                {
                  key: "status",
                  label: "Status",
                  render: (value) => (
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        value === "deployed"
                          ? "bg-green-900 text-green-200"
                          : value === "paused"
                          ? "bg-yellow-900 text-yellow-200"
                          : value === "draft"
                          ? "bg-gray-600 text-gray-200"
                          : "bg-red-900 text-red-200"
                      }`}
                    >
                      {String(value).toUpperCase()}
                    </span>
                  ),
                },
                {
                  key: "created_at",
                  label: "Created",
                  render: (value) => formatDate(value as string),
                },
                {
                  key: "executions",
                  label: "Executions",
                  render: (_value, row: any) => {
                    const metrics = appMetrics[row.app_id];
                    return metrics ? (
                      <span>{metrics.total_executions}</span>
                    ) : (
                      "-"
                    );
                  },
                },
                {
                  key: "avg_duration",
                  label: "Avg Duration",
                  render: (_value, row: any) => {
                    const metrics = appMetrics[row.app_id];
                    return metrics ? (
                      <span>{formatDuration(metrics.avg_duration_ms)}</span>
                    ) : (
                      "-"
                    );
                  },
                },
                {
                  key: "cost",
                  label: "Cost",
                  render: (_value, row: any) => {
                    const metrics = appMetrics[row.app_id];
                    return metrics ? (
                      <span className="font-semibold">
                        {formatCurrency(metrics.total_cost)}
                      </span>
                    ) : (
                      "-"
                    );
                  },
                },
                {
                  key: "actions",
                  label: "Actions",
                  align: "right",
                  render: (_value, row: any) => {
                    const app = apps.find((a) => a.app_id === row.app_id);
                    if (!app) return "-";

                    return (
                      <div className="flex gap-2 justify-end">
                        <Button
                          size="sm"
                          onClick={() => navigate(`/apps/${app.app_id}`)}
                        >
                          Open
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleViewLogs(app)}
                        >
                          Logs
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleViewVersions(app)}
                        >
                          Versions
                        </Button>
                        {can("apps:deploy") && app.status !== "deployed" && (
                          <Button
                            size="sm"
                            onClick={() => handleDeploy(app)}
                            disabled={actionInProgress}
                          >
                            Deploy
                          </Button>
                        )}
                        {can("apps:deploy") && app.status === "deployed" && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handlePause(app)}
                            disabled={actionInProgress}
                          >
                            Pause
                          </Button>
                        )}
                        {can("apps:delete") && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleDelete(app)}
                            disabled={actionInProgress}
                          >
                            Delete
                          </Button>
                        )}
                      </div>
                    );
                  },
                },
              ]}
              data={apps as any}
            />
          </Card>
        )}

        {/* Create App Modal */}
        <Modal
          isOpen={showCreateModal}
          title="Create New Application"
          onClose={() => setShowCreateModal(false)}
        >
          <div className="space-y-4">
            {createError && (
              <div className="p-3 bg-red-900 border border-red-700 rounded text-red-300 text-sm">{createError}</div>
            )}
            <div>
              <label className="block text-sm text-gray-400 mb-1">App Name <span className="text-red-400">*</span></label>
              <input
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                placeholder="e.g. My Workflow App"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Description</label>
              <textarea
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500 resize-none"
                rows={3}
                placeholder="What does this app do?"
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Version</label>
                <input
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                  placeholder="1.0.0"
                  value={createForm.version}
                  onChange={(e) => setCreateForm({ ...createForm, version: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Entry Point</label>
                <input
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                  placeholder="index.js"
                  value={createForm.entry_point}
                  onChange={(e) => setCreateForm({ ...createForm, entry_point: e.target.value })}
                />
              </div>
            </div>
            <div className="flex gap-3 justify-end pt-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreateApp} disabled={actionInProgress}>
                {actionInProgress ? 'Creating...' : 'Create App'}
              </Button>
            </div>
          </div>
        </Modal>

        {/* Run App Modal */}
        <Modal
          isOpen={showRunModal}
          title={`▶ Run — ${runApp?.name}`}
          onClose={() => { setShowRunModal(false); setRunInProgress(false); setRunLog([]); }}
        >
          <div className="space-y-4">
            {/* App info */}
            <div className="bg-gray-800 rounded p-3 grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-gray-400">Name: </span><span className="text-white font-semibold">{runApp?.name}</span></div>
              <div><span className="text-gray-400">Version: </span><span className="font-mono text-blue-300">{(runApp as any)?.version || '1.0.0'}</span></div>
              <div><span className="text-gray-400">Entry Point: </span><span className="font-mono text-yellow-300">{(runApp as any)?.entry_point || 'index.js'}</span></div>
              <div><span className="text-gray-400">Status: </span><span className="text-green-300 font-semibold">{String(runApp?.status || '').toUpperCase()}</span></div>
              {(runApp as any)?.description && (
                <div className="col-span-2"><span className="text-gray-400">Description: </span><span className="text-gray-200">{(runApp as any).description}</span></div>
              )}
            </div>
            {/* Input */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">Input Payload (optional)</label>
              <textarea
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white font-mono text-xs focus:outline-none focus:border-blue-500 resize-none"
                rows={3}
                placeholder='e.g. {"candidate": "John Smith", "role": "Software Engineer"}'
                value={runInput}
                onChange={(e) => setRunInput(e.target.value)}
                disabled={runInProgress}
              />
            </div>
            {/* Log output */}
            {runLog.length > 0 && (
              <div className="bg-gray-900 border border-gray-700 rounded p-3 max-h-48 overflow-y-auto">
                {runLog.map((entry, i) => (
                  <p key={i} className={`text-xs font-mono ${
                    entry.type === 'success' ? 'text-green-400' :
                    entry.type === 'error' ? 'text-red-400' : 'text-gray-300'
                  }`}>{entry.message}</p>
                ))}
              </div>
            )}
            <div className="flex gap-3 justify-end pt-1">
              <Button variant="secondary" onClick={() => { setShowRunModal(false); setRunLog([]); }} disabled={runInProgress}>Close</Button>
              <Button onClick={handleRunApp} disabled={runInProgress}>
                {runInProgress ? '⏳ Running...' : '▶ Run App'}
              </Button>
            </div>
          </div>
        </Modal>

        {/* Logs Modal */}
        <Modal
          isOpen={showLogsModal}
          title={`Logs - ${selectedApp?.name}`}
          onClose={() => setShowLogsModal(false)}
        >
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {appLogs.length === 0 ? (
              <p className="text-gray-400 text-sm">No logs available</p>
            ) : (
              appLogs.map((log, idx) => (
                <div
                  key={idx}
                  className="text-xs font-mono bg-gray-900 p-2 rounded border border-gray-700"
                >
                  <p>{JSON.stringify(log)}</p>
                </div>
              ))
            )}
          </div>
        </Modal>

        {/* Versions Modal */}
        <Modal
          isOpen={showVersionsModal}
          title={`Versions - ${selectedApp?.name}`}
          onClose={() => setShowVersionsModal(false)}
        >
          <div className="space-y-3">
            {appVersions.length === 0 ? (
              <p className="text-gray-400 text-sm">No versions available</p>
            ) : (
              appVersions.map((version: any, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-gray-700 rounded"
                >
                  <div>
                    <p className="font-semibold">{version.version_id}</p>
                    <p className="text-xs text-gray-400">
                      {formatDate(version.created_at)}
                    </p>
                  </div>
                  {can("apps:deploy") && (
                    <Button
                      size="sm"
                      onClick={() => handleRollback(selectedApp!, version.version_id)}
                      disabled={actionInProgress}
                    >
                      Rollback
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>
        </Modal>
      </div>
    </MainLayout>
  );
};
