/**
 * Platform Admin Console Page
 * Global view: tenant registry, health, SLA, revenue, worker pool
 */

import React, { useState, useEffect } from "react";
import { MainLayout } from "../components/layouts/MainLayout";
import {
  Card,
  Stat,
  Button,
  Loading,
  ErrorAlert,
  ProgressBar,
  Table,
  EmptyState,
} from "../components/common/UIComponents";
import { useMetrics } from "../hooks";
import { tenantService, metricsService } from "../services";
import { formatCurrency, formatNumberCompact, formatPercentage } from "../utils";
import type { Tenant, PaginatedResponse } from "../types";

export const PlatformAdminConsole: React.FC = () => {
  const { platformHealth, isLoading: metricsLoading } = useMetrics({
    pollInterval: 60000,
  });

  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [stats, setStats] = useState<{
    total_tenants: number;
    active_executions: number;
    revenue_month: number;
    uptime_percent: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPlatformData = async () => {
      setLoading(true);
      setError(null);

      try {
        const tenantResult = await tenantService.listTenants(50);
        setTenants(tenantResult.items);

        // Calculate stats
        let totalRevenue = 0;
        const plans: Record<string, number> = {
          free: 0,
          starter: 49,
          professional: 299,
          enterprise: 500, // estimated
        };

        tenantResult.items.forEach((t) => {
          totalRevenue += plans[t.subscription_plan] || 0;
        });

        setStats({
          total_tenants: tenantResult.total,
          active_executions: platformHealth?.active_executions || 0,
          revenue_month: totalRevenue,
          uptime_percent: platformHealth?.uptime_percent || 0,
        });
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load platform data"
        );
      } finally {
        setLoading(false);
      }
    };

    loadPlatformData();
  }, [platformHealth]);

  if (loading) return <Loading text="Loading platform admin console..." />;

  return (
    <MainLayout
      title="Platform Admin Console"
      breadcrumbs={[
        { label: "Admin", href: "/admin" },
        { label: "Platform Overview" },
      ]}
    >
      <div className="space-y-6">
        {error && <ErrorAlert message={error} />}

        {/* Platform KPIs */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Stat
              label="Active Tenants"
              value={stats.total_tenants}
              trend="up"
              trendValue="+12% this month"
              icon="🏢"
            />
            <Stat
              label="Monthly Revenue"
              value={formatCurrency(stats.revenue_month)}
              trend="up"
              trendValue="+25% growth"
              icon="💰"
            />
            <Stat
              label="Active Executions"
              value={formatNumberCompact(stats.active_executions)}
              icon="▶️"
            />
            <Stat
              label="Platform Uptime"
              value={formatPercentage(stats.uptime_percent)}
              trend={stats.uptime_percent >= 99.9 ? "up" : "down"}
              icon="💚"
            />
          </div>
        )}

        {/* Platform Health & SLA */}
        {platformHealth && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Health Overview */}
            <Card title="Platform Health">
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-300">System Status</span>
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        platformHealth.status === "healthy"
                          ? "bg-green-900 text-green-200"
                          : platformHealth.status === "degraded"
                          ? "bg-yellow-900 text-yellow-200"
                          : "bg-red-900 text-red-200"
                      }`}
                    >
                      {platformHealth.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-300">Uptime SLA</span>
                    <span className="text-sm text-gray-400">
                      {formatPercentage(platformHealth.uptime_percent)}
                    </span>
                  </div>
                  <ProgressBar
                    value={platformHealth.uptime_percent}
                    max={100}
                    color={platformHealth.uptime_percent >= 99.9 ? "green" : "red"}
                    showPercentage={false}
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-300">Response Time P99</span>
                    <span className="text-sm text-gray-400">
                      {platformHealth.response_time_p99_ms}ms
                    </span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-300">Error Rate</span>
                    <span className="text-sm text-gray-400">
                      {formatPercentage(platformHealth.error_rate_percent)}
                    </span>
                  </div>
                  <ProgressBar
                    value={Math.min(platformHealth.error_rate_percent, 1)}
                    max={1}
                    color={platformHealth.error_rate_percent <= 0.1 ? "green" : "red"}
                    showPercentage={false}
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-300">Cache Hit Rate</span>
                    <span className="text-sm text-gray-400">
                      {formatPercentage(platformHealth.cache_hit_rate)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Worker Pool */}
            <Card title="Worker Pool Management">
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-300">
                      Database Connections
                    </span>
                    <span className="text-sm text-gray-400">
                      {platformHealth.database_connections.used} /{" "}
                      {platformHealth.database_connections.total}
                    </span>
                  </div>
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
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-300">
                      Worker Pool Utilization
                    </span>
                    <span className="text-sm text-gray-400">
                      {formatPercentage(platformHealth.worker_pool_utilization)}
                    </span>
                  </div>
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
                </div>

                <div>
                  <p className="text-sm text-gray-300 mb-2">Status</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-gray-700 p-2 rounded">
                      <p className="text-gray-400">Active Tenants</p>
                      <p className="font-bold text-lg">
                        {platformHealth.active_tenants}
                      </p>
                    </div>
                    <div className="bg-gray-700 p-2 rounded">
                      <p className="text-gray-400">Active Jobs</p>
                      <p className="font-bold text-lg">
                        {platformHealth.active_executions}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Tenant Registry */}
        <Card
          title="Tenant Registry"
          description="Overview of all tenants on the platform"
        >
          {tenants.length === 0 ? (
            <EmptyState
              icon="🏢"
              title="No Tenants"
              description="No tenants onboarded yet"
            />
          ) : (
            <Table
              columns={[
                {
                  key: "organization_name",
                  label: "Organization",
                  render: (value, row: any) => (
                    <div>
                      <p className="font-semibold">{value}</p>
                      <p className="text-xs text-gray-400">{row.tenant_id}</p>
                    </div>
                  ),
                },
                {
                  key: "status",
                  label: "Status",
                  render: (value) => (
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        value === "active"
                          ? "bg-green-900 text-green-200"
                          : value === "suspended"
                          ? "bg-red-900 text-red-200"
                          : "bg-blue-900 text-blue-200"
                      }`}
                    >
                      {String(value).toUpperCase()}
                    </span>
                  ),
                },
                {
                  key: "subscription_plan",
                  label: "Plan",
                  render: (value) => (
                    <span className="capitalize font-medium">
                      {String(value)}
                    </span>
                  ),
                },
                {
                  key: "owner_email",
                  label: "Owner Email",
                  render: (value) => (
                    <span className="text-sm">{value}</span>
                  ),
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
                {
                  key: "tenant_id",
                  label: "Actions",
                  align: "right",
                  render: (value) => (
                    <div className="flex gap-2">
                      <Button variant="secondary" size="sm">
                        View Details
                      </Button>
                      <Button variant="secondary" size="sm">
                        Manage
                      </Button>
                    </div>
                  ),
                },
              ]}
              data={tenants}
            />
          )}
        </Card>

        {/* Revenue & Usage Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Revenue Breakdown */}
          <Card title="Revenue Breakdown">
            <div className="space-y-3">
              {["free", "starter", "professional", "enterprise"].map((plan) => {
                const count = tenants.filter(
                  (t) => t.subscription_plan === plan
                ).length;
                const planPrices: Record<string, number> = {
                  free: 0,
                  starter: 49,
                  professional: 299,
                  enterprise: 500,
                };
                const revenue = count * (planPrices[plan] || 0);

                return (
                  <div key={plan}>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm text-gray-300 capitalize">
                        {plan} Plan
                      </span>
                      <span className="text-sm font-semibold">
                        {count} tenants · {formatCurrency(revenue)}
                      </span>
                    </div>
                    <ProgressBar
                      value={count}
                      max={Math.max(
                        ...tenants
                          .map((t) => t.subscription_plan)
                          .reduce((acc: Record<string, number>, p) => {
                            acc[p] = (acc[p] || 0) + 1;
                            return acc;
                          }, {})
                          .values()
                      )}
                      showPercentage={false}
                      color="blue"
                    />
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Top Tenants by Usage */}
          <Card title="Platform Alerts">
            <div className="space-y-2">
              <div className="bg-red-900 border border-red-700 rounded p-3">
                <p className="text-sm font-semibold text-red-200">
                  ⚠️ Critical Alert
                </p>
                <p className="text-xs text-red-100">
                  Worker pool utilization above 80%
                </p>
              </div>
              <div className="bg-yellow-900 border border-yellow-700 rounded p-3">
                <p className="text-sm font-semibold text-yellow-200">
                  ⚠️ Warning
                </p>
                <p className="text-xs text-yellow-100">
                  Database connection pool at 75% capacity
                </p>
              </div>
              <div className="bg-blue-900 border border-blue-700 rounded p-3">
                <p className="text-sm font-semibold text-blue-200">
                  ℹ️ Info
                </p>
                <p className="text-xs text-blue-100">
                  Scheduled maintenance: Next Tuesday at 2 AM UTC
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* System Configuration */}
        <Card title="Platform Configuration">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-700 rounded p-4">
              <p className="text-xs text-gray-400 mb-1">API Version</p>
              <p className="font-semibold">v1.0.0</p>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <p className="text-xs text-gray-400 mb-1">Database</p>
              <p className="font-semibold">PostgreSQL 15</p>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <p className="text-xs text-gray-400 mb-1">Cache</p>
              <p className="font-semibold">Redis 7.0</p>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <p className="text-xs text-gray-400 mb-1">Region</p>
              <p className="font-semibold">US-EAST-1</p>
            </div>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
};
