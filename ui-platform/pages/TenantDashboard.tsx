/**
 * Tenant Dashboard Page
 * Overview, usage, billing, metrics, resources for current tenant
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MainLayout } from "../components/layouts/MainLayout";
import {
  Card,
  Stat,
  Button,
  Loading,
  ErrorAlert,
  ProgressBar,
} from "../components/common/UIComponents";
import { useAuth, useTenant, useMetrics, usePermission } from "../hooks";
import {
  tenantService,
  billingService,
  metricsService,
} from "../services";
import {
  formatCurrency,
  formatNumberCompact,
  formatBytes,
  formatPercentage,
} from "../utils";
import type { QuotaUsage, Subscription } from "../types";

export const TenantDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { tenant: companyTenant } = useAuth();
  const { quota } = useTenant();
  const { tenantMetrics, platformHealth, isLoading: metricsLoading } =
    useMetrics();
  const { can } = usePermission();

  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [quotaUsage, setQuotaUsage] = useState<QuotaUsage | null>(null);
  const [costs, setCosts] = useState<{
    total: number;
    daily_breakdown: Array<{ date: string; cost: number }>;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI App creation prompt
  const [appPrompt, setAppPrompt] = useState("");
  const [promptError, setPromptError] = useState("");

  const handleLaunchOrchestrator = () => {
    if (!appPrompt.trim()) {
      setPromptError("Please describe the app you want to build first.");
      return;
    }
    setPromptError("");
    navigate("/orchestrator", { state: { prompt: appPrompt.trim() } });
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [sub, costData] = await Promise.all([
          billingService.getSubscription(),
          metricsService.getCostMetrics(),
        ]);

        setSubscription(sub);
        setCosts({
          total: costData.total_cost,
          daily_breakdown: costData.daily_breakdown,
        });

        // Calculate quota usage
        if (quota) {
          setQuotaUsage({
            apps: {
              used: 0, // Would be fetched from metrics
              limit: quota.max_apps,
              percentage: 0,
            },
            workflows: {
              used: 0,
              limit: quota.max_workflows_per_app,
              percentage: 0,
            },
            api_calls: {
              used: tenantMetrics?.executions_count || 0,
              limit: quota.max_api_calls_per_month,
              percentage: tenantMetrics
                ? (tenantMetrics.executions_count / quota.max_api_calls_per_month) * 100
                : 0,
            },
            storage: {
              used: tenantMetrics?.storage_used_gb || 0,
              limit: quota.max_storage_gb,
              percentage: tenantMetrics
                ? (tenantMetrics.storage_used_gb / quota.max_storage_gb) * 100
                : 0,
            },
            concurrent_connections: {
              used: 0,
              limit: quota.max_concurrent_connections,
              percentage: 0,
            },
            users: {
              used: 0,
              limit: quota.max_users,
              percentage: 0,
            },
          });
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load dashboard data"
        );
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [quota, tenantMetrics]);

  if (loading) return <Loading text="Loading dashboard..." />;

  return (
    <MainLayout
      title="Tenant Dashboard"
      breadcrumbs={[
        { label: "Dashboard", href: "/dashboard" },
      ]}
    >
      <div className="space-y-6">
        {error && <ErrorAlert message={error} />}

        {/* ─── CREATE AUTONOMOUS AI APP ─────────────────────────────────── */}
        <div
          className="rounded-xl border border-blue-800/50 bg-gray-800/60 p-6"
          style={{ boxShadow: "0 0 0 1px rgba(59,130,246,0.08), 0 4px 32px rgba(59,130,246,0.07)" }}
        >
          {/* Header */}
          <div className="flex items-center gap-3 mb-1">
            <span className="text-blue-400 text-xl" aria-hidden>⬡</span>
            <h2 className="text-lg font-semibold text-white tracking-tight">
              Create Autonomous AI App
            </h2>
          </div>
          <p className="text-sm text-gray-400 mb-5 ml-9">
            Build and deploy AI-native business apps from a single prompt.
          </p>

          {/* Prompt input */}
          <textarea
            rows={3}
            className="w-full px-4 py-3 bg-gray-900 border rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-1 resize-none transition-colors"
            style={{
              borderColor: promptError ? "#f87171" : "rgba(59,130,246,0.35)",
            }}
            onFocus={(e) =>
              (e.currentTarget.style.borderColor = promptError
                ? "#f87171"
                : "rgba(96,165,250,0.7)")
            }
            onBlur={(e) =>
              (e.currentTarget.style.borderColor = promptError
                ? "#f87171"
                : "rgba(59,130,246,0.35)")
            }
            placeholder={`Describe the business app you want to build...\ne.g. "A payroll processor that calculates net salary, tax deductions, and generates payslips"`}
            value={appPrompt}
            onChange={(e) => {
              setAppPrompt(e.target.value);
              if (promptError) setPromptError("");
            }}
          />

          {/* Validation */}
          {promptError && (
            <p className="text-red-400 text-xs mt-1.5">{promptError}</p>
          )}

          {/* Action row */}
          <div className="flex items-center justify-between mt-4">
            <span className="text-xs text-gray-600">
              Powered by GPT-4o-mini orchestration pipeline
            </span>
            <button
              onClick={handleLaunchOrchestrator}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50"
            >
              <span>Launch Orchestrator</span>
              <span aria-hidden>→</span>
            </button>
          </div>
        </div>

        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat
            label="Organization"
            value={companyTenant?.organization_name || "N/A"}
            icon="🏢"
          />
          <Stat
            label="Current Plan"
            value={subscription?.plan.toUpperCase() || "N/A"}
            icon="📋"
          />
          <Stat
            label="Total Cost (Month)"
            value={formatCurrency(costs?.total || 0)}
            icon="💰"
          />
          {platformHealth && (
            <Stat
              label="Platform Status"
              value={platformHealth.status.toUpperCase()}
              trend={
                platformHealth.status === "healthy"
                  ? "up"
                  : platformHealth.status === "degraded"
                  ? "stable"
                  : "down"
              }
              icon={
                platformHealth.status === "healthy"
                  ? "✅"
                  : platformHealth.status === "degraded"
                  ? "⚠️"
                  : "❌"
              }
            />
          )}
        </div>

        {/* Metrics Overview */}
        {tenantMetrics && (
          <Card title="Usage Metrics">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-400 mb-2">Total Executions</p>
                <p className="text-2xl font-bold">
                  {formatNumberCompact(tenantMetrics.executions_count)}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Success Rate: {formatPercentage(tenantMetrics.success_rate)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-400 mb-2">Storage Used</p>
                <p className="text-2xl font-bold">
                  {formatBytes(tenantMetrics.storage_used_gb * 1024 * 1024 * 1024)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-400 mb-2">Avg Duration</p>
                <p className="text-2xl font-bold">
                  {tenantMetrics.avg_execution_duration_ms}ms
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Quota Usage */}
        {quotaUsage && (
          <Card title="Quota Usage">
            <div className="space-y-4">
              {Object.entries(quotaUsage).map(([key, value]) => (
                <div key={key}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-gray-300 capitalize">
                      {key.replace(/_/g, " ")}
                    </p>
                    <p className="text-sm text-gray-400">
                      {typeof value.limit === "string"
                        ? "Unlimited"
                        : `${value.used} / ${value.limit}`}
                    </p>
                  </div>
                  {typeof value.limit === "number" && (
                    <ProgressBar
                      value={value.used}
                      max={value.limit}
                      color={
                        value.percentage > 90
                          ? "red"
                          : value.percentage > 75
                          ? "yellow"
                          : "green"
                      }
                      showPercentage={false}
                    />
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Billing & API Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Billing Card */}
          <Card
            title="Billing Information"
            headerAction={
              can("billing:write") && (
                <Button variant="secondary" size="sm">
                  Manage
                </Button>
              )
            }
          >
            {subscription && (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Current Plan:</span>
                  <span className="font-semibold">
                    {subscription.plan.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Billing Cycle:</span>
                  <span className="font-semibold text-sm">
                    {new Date(subscription.billing_cycle_start).toLocaleDateString()} -{" "}
                    {new Date(subscription.billing_cycle_end).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Status:</span>
                  <span
                    className={`font-semibold ${
                      subscription.status === "active"
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    {subscription.status.toUpperCase()}
                  </span>
                </div>
                <div className="pt-3 border-t border-gray-700">
                  {can("billing:read") && (
                    <Button size="sm" className="w-full">
                      View Invoices
                    </Button>
                  )}
                </div>
              </div>
            )}
          </Card>

          {/* LLM Tokens Card */}
          <Card title="API & LLM Token Usage">
            {tenantMetrics && (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-400 mb-2">Total API Calls</p>
                  <p className="text-2xl font-bold">
                    {formatNumberCompact(tenantMetrics.api_calls_total)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400 mb-2">Failed Executions</p>
                  <p className="text-lg font-semibold">
                    {tenantMetrics.executions_failed}
                  </p>
                </div>
                <Button size="sm" className="w-full">
                  View Details
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* Resource Allocation */}
        <Card title="Resource Allocation">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-300">Database Connections</span>
                {platformHealth && (
                  <span className="text-sm text-gray-400">
                    {platformHealth.database_connections.used} /{" "}
                    {platformHealth.database_connections.total}
                  </span>
                )}
              </div>
              {platformHealth && (
                <ProgressBar
                  value={platformHealth.database_connections.used}
                  max={platformHealth.database_connections.total}
                  color={
                    (platformHealth.database_connections.used /
                      platformHealth.database_connections.total) *
                      100 >
                    80
                      ? "red"
                      : "blue"
                  }
                  showPercentage={false}
                />
              )}
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-300">Worker Pool Utilization</span>
                {platformHealth && (
                  <span className="text-sm text-gray-400">
                    {formatPercentage(platformHealth.worker_pool_utilization)}
                  </span>
                )}
              </div>
              {platformHealth && (
                <ProgressBar
                  value={platformHealth.worker_pool_utilization}
                  max={100}
                  color={
                    platformHealth.worker_pool_utilization > 80
                      ? "red"
                      : platformHealth.worker_pool_utilization > 60
                      ? "yellow"
                      : "green"
                  }
                  showPercentage={false}
                />
              )}
            </div>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
};
