/**
 * Observability Dashboard Page
 * Real-time metrics, errors, latency, costs, SLA
 */

import React, { useState, useEffect } from "react";
import { MainLayout } from "../components/layouts/MainLayout";
import {
  Card,
  Stat,
  Loading,
  ErrorAlert,
  Table,
  ProgressBar,
} from "../components/common/UIComponents";
import { useMetrics } from "../hooks";
import { metricsService } from "../services";
import {
  formatCurrency,
  formatNumberCompact,
  formatDuration,
  formatPercentage,
} from "../utils";
import type { Alert, ExecutionMetric } from "../types";

export const ObservabilityDashboard: React.FC = () => {
  const {
    tenantMetrics,
    platformHealth,
    isLoading: metricsLoading,
  } = useMetrics({ pollInterval: 30000 });

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [executionMetrics, setExecutionMetrics] = useState<ExecutionMetric[]>([]);
  const [costsData, setCostsData] = useState<{
    total_cost: number;
    daily_breakdown: Array<{ date: string; cost: number }>;
  } | null>(null);
  const [slaMetrics, setSLAMetrics] = useState<{
    uptime_percent: number;
    response_time_p99_ms: number;
    error_rate_percent: number;
    period: { start: string; end: string };
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMetrics = async () => {
      setLoading(true);
      setError(null);

      try {
        const [alertsData, execMetrics, costs, sla] = await Promise.all([
          metricsService.getAlerts(undefined, undefined, 10),
          metricsService.getExecutionMetrics(undefined, 20),
          metricsService.getCostMetrics(),
          metricsService.getSLAMetrics(),
        ]);

        setAlerts(alertsData.items);
        setExecutionMetrics(execMetrics.items);
        setCostsData(costs);
        setSLAMetrics(sla);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load observability data"
        );
      } finally {
        setLoading(false);
      }
    };

    loadMetrics();
  }, []);

  if (loading) return <Loading text="Loading observability data..." />;

  return (
    <MainLayout
      title="Observability Dashboard"
      breadcrumbs={[
        { label: "Dashboard", href: "/dashboard" },
        { label: "Observability" },
      ]}
    >
      <div className="space-y-6">
        {error && <ErrorAlert message={error} />}

        {/* Platform Health Overview */}
        {platformHealth && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Stat
              label="Platform Status"
              value={platformHealth.status.toUpperCase()}
              icon={
                platformHealth.status === "healthy"
                  ? "✅"
                  : platformHealth.status === "degraded"
                  ? "⚠️"
                  : "❌"
              }
              trend={platformHealth.status === "healthy" ? "up" : "down"}
            />
            <Stat
              label="Uptime"
              value={formatPercentage(platformHealth.uptime_percent)}
              icon="💚"
            />
            <Stat
              label="Response Time (P99)"
              value={formatDuration(platformHealth.response_time_p99_ms)}
              icon="⚡"
              trend={platformHealth.response_time_p99_ms < 100 ? "up" : "down"}
            />
            <Stat
              label="Error Rate"
              value={formatPercentage(platformHealth.error_rate_percent)}
              icon={platformHealth.error_rate_percent < 1 ? "✅" : "❌"}
            />
          </div>
        )}

        {/* Metrics Overview */}
        {tenantMetrics && (
          <Card title="Execution Metrics">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Stat
                label="Total Executions"
                value={formatNumberCompact(tenantMetrics.executions_count)}
                trend="up"
                trendValue={`+${tenantMetrics.executions_count} this period`}
                icon="▶️"
              />
              <Stat
                label="Failed Executions"
                value={tenantMetrics.executions_failed}
                trend={tenantMetrics.executions_failed > 0 ? "down" : "stable"}
                trendValue={`${formatPercentage(
                  (tenantMetrics.executions_failed / tenantMetrics.executions_count) * 100
                )} of total`}
                icon="❌"
              />
              <Stat
                label="Success Rate"
                value={formatPercentage(tenantMetrics.success_rate)}
                trend={tenantMetrics.success_rate > 98 ? "up" : "down"}
                trendValue={`Target: 99%`}
                icon="📊"
              />
              <Stat
                label="Avg Duration"
                value={formatDuration(tenantMetrics.avg_execution_duration_ms)}
                trend={tenantMetrics.avg_execution_duration_ms < 500 ? "up" : "down"}
                icon="⏱️"
              />
            </div>
          </Card>
        )}

        {/* SLA Metrics */}
        {slaMetrics && (
          <Card title="SLA Compliance">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-300">Uptime SLA</span>
                  <span className="text-sm text-gray-400">Target: 99.9%</span>
                </div>
                <ProgressBar
                  value={slaMetrics.uptime_percent}
                  max={99.9}
                  color={slaMetrics.uptime_percent >= 99.9 ? "green" : "yellow"}
                  showPercentage={false}
                  label={`${formatPercentage(slaMetrics.uptime_percent)}`}
                />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-300">Response Time P99</span>
                  <span className="text-sm text-gray-400">Target: &lt;100ms</span>
                </div>
                <ProgressBar
                  value={Math.min(slaMetrics.response_time_p99_ms, 100)}
                  max={100}
                  color={slaMetrics.response_time_p99_ms <= 100 ? "green" : "red"}
                  showPercentage={false}
                  label={`${formatDuration(slaMetrics.response_time_p99_ms)}`}
                />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-300">Error Rate</span>
                  <span className="text-sm text-gray-400">Target: &lt;0.1%</span>
                </div>
                <ProgressBar
                  value={Math.min(slaMetrics.error_rate_percent, 1)}
                  max={1}
                  color={slaMetrics.error_rate_percent <= 0.1 ? "green" : "red"}
                  showPercentage={false}
                  label={`${formatPercentage(slaMetrics.error_rate_percent)}`}
                />
              </div>
            </div>
          </Card>
        )}

        {/* Cost Analysis */}
        {costsData && (
          <Card title="Cost Analysis">
            <div className="mb-4">
              <p className="text-sm text-gray-400">Total Monthly Cost</p>
              <p className="text-3xl font-bold">
                {formatCurrency(costsData.total_cost)}
              </p>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <p className="text-xs text-gray-400 mb-3">Daily Breakdown</p>
              <div className="flex items-end space-x-1 h-32">
                {costsData.daily_breakdown.map((day, idx) => (
                  <div
                    key={idx}
                    className="flex-1 bg-blue-600 rounded-t hover:bg-blue-500 cursor-pointer relative group"
                    style={{
                      height: `${
                        (day.cost /
                          Math.max(...costsData.daily_breakdown.map((d) => d.cost))) *
                        100
                      }%`,
                      minHeight: "4px",
                    }}
                  >
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 bg-gray-900 text-xs text-white px-2 py-1 rounded mb-1 opacity-0 group-hover:opacity-100 whitespace-nowrap">
                      {day.date}: {formatCurrency(day.cost)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Active Alerts */}
        <Card title="Active Alerts" description="Recent platform and tenant alerts">
          {alerts.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400">No active alerts 🎉</p>
            </div>
          ) : (
            <Table
              columns={[
                {
                  key: "title",
                  label: "Alert",
                  render: (value) => <span className="font-medium">{value}</span>,
                },
                {
                  key: "severity",
                  label: "Severity",
                  render: (value) => (
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        value === "critical"
                          ? "bg-red-900 text-red-200"
                          : value === "warning"
                          ? "bg-yellow-900 text-yellow-200"
                          : "bg-blue-900 text-blue-200"
                      }`}
                    >
                      {String(value).toUpperCase()}
                    </span>
                  ),
                },
                {
                  key: "metric_value",
                  label: "Value / Threshold",
                  align: "right",
                  render: (value, row: any) =>
                    `${value} / ${row.threshold}`,
                },
                {
                  key: "created_at",
                  label: "Created",
                  render: (value) => (
                    <span className="text-sm">
                      {new Date(value as string).toLocaleDateString()}
                    </span>
                  ),
                },
              ]}
              data={alerts}
            />
          )}
        </Card>

        {/* Recent Executions */}
        <Card title="Recent Executions">
          {executionMetrics.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400">No recent executions</p>
            </div>
          ) : (
            <Table
              columns={[
                {
                  key: "execution_id",
                  label: "Execution",
                  render: (value) => (
                    <span className="font-mono text-xs">
                      {String(value).substring(0, 8)}...
                    </span>
                  ),
                },
                {
                  key: "status",
                  label: "Status",
                  render: (value) => (
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        value === "completed"
                          ? "bg-green-900 text-green-200"
                          : value === "failed"
                          ? "bg-red-900 text-red-200"
                          : "bg-blue-900 text-blue-200"
                      }`}
                    >
                      {String(value).toUpperCase()}
                    </span>
                  ),
                },
                {
                  key: "duration_ms",
                  label: "Duration",
                  align: "right",
                  render: (value) => formatDuration(Number(value)),
                },
                {
                  key: "cost",
                  label: "Cost",
                  align: "right",
                  render: (value) => formatCurrency(Number(value)),
                },
                {
                  key: "timestamp",
                  label: "Time",
                  render: (value) => (
                    <span className="text-sm">
                      {new Date(value as string).toLocaleTimeString()}
                    </span>
                  ),
                },
              ]}
              data={executionMetrics}
            />
          )}
        </Card>
      </div>
    </MainLayout>
  );
};
