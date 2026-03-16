/**
 * Billing Dashboard Page
 * Current plan, usage vs quota, overages, invoices
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
import { useAuth, usePermission } from "../hooks";
import { billingService } from "../services";
import { formatCurrency, formatDate, formatPercentage } from "../utils";
import { SUBSCRIPTION_PLANS } from "../utils";
import type { Subscription, Invoice, BillingEvents } from "../types";

export const BillingDashboard: React.FC = () => {
  const { tenant } = useAuth();
  const { can } = usePermission();

  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [billingEvents, setBillingEvents] = useState<BillingEvents | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadBillingData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [sub, invoiceData, events] = await Promise.all([
          billingService.getSubscription(),
          billingService.getInvoices(undefined, 5),
          billingService.getBillingEvents(),
        ]);

        setSubscription(sub);
        setInvoices(invoiceData.items);
        setBillingEvents(events);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load billing data");
      } finally {
        setLoading(false);
      }
    };

    loadBillingData();
  }, []);

  const currentPlan =
    subscription && (SUBSCRIPTION_PLANS as any)[subscription.plan];

  if (loading) return <Loading text="Loading billing data..." />;

  return (
    <MainLayout
      title="Billing Dashboard"
      breadcrumbs={[
        { label: "Dashboard", href: "/dashboard" },
        { label: "Billing" },
      ]}
    >
      <div className="space-y-6">
        {error && <ErrorAlert message={error} />}

        {/* Current Plan Overview */}
        {subscription && currentPlan && (
          <Card
            title="Current Subscription"
            headerAction={
              can("billing:write") && (
                <Button variant="secondary" size="sm">
                  Change Plan
                </Button>
              )
            }
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <Stat
                label="Plan"
                value={currentPlan.name}
                icon="📋"
              />
              <Stat
                label="Monthly Price"
                value={formatCurrency(currentPlan.price || 0)}
                icon="💰"
              />
              <Stat
                label="Status"
                value={subscription.status.toUpperCase()}
                icon={subscription.status === "active" ? "✅" : "⚠️"}
              />
            </div>

            <div className="border-t border-gray-700 pt-4">
              <p className="text-sm font-semibold mb-3">Plan Features</p>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(currentPlan.features || {}).map(
                  ([feature, limit]) => (
                    <div key={feature} className="text-sm">
                      <span className="text-gray-400">{feature.replace(/_/g, " ")}:</span>
                      <span className="text-gray-200 ml-2 font-medium">
                        {typeof limit === "number" ? limit : limit}
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>
          </Card>
        )}

        {/* Usage Summary */}
        {billingEvents && (
          <Card title="Usage Summary">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Stat
                label="Total Executions"
                value={billingEvents.total_executions}
                trend="up"
                trendValue={`${formatPercentage(billingEvents.success_rate ?? 0)} success`}
                icon="▶️"
              />
              <Stat
                label="Failed Executions"
                value={billingEvents.failed_executions}
                trend={
                  billingEvents.failed_executions > 0 ? "down" : "stable"
                }
                icon="❌"
              />
              <Stat
                label="API Calls"
                value={billingEvents.api_calls}
                trend="up"
                trendValue={`Avg ${billingEvents.avg_execution_duration_ms}ms`}
                icon="🔗"
              />
              <Stat
                label="Storage Used"
                value={`${billingEvents.storage_used_gb}GB`}
                icon="💾"
              />
              <Stat
                label="Success Rate"
                value={formatPercentage(billingEvents.success_rate)}
                trend="up"
                icon="📊"
              />
              <Stat
                label="Estimated Monthly Cost"
                value={formatCurrency(billingEvents.total_cost)}
                icon="💸"
              />
            </div>
          </Card>
        )}

        {/* Quota vs Usage */}
        <Card
          title="Quotas & Limits"
          description="Current usage against your plan limits"
        >
          {subscription && currentPlan && (
            <div className="space-y-4">
              {Object.entries(currentPlan.features || {}).map(
                ([feature, limit]) => {
                  const used =
                    (subscription.current_period_usage[feature] || 0) as number;
                  const limitNum = typeof limit === "number" ? limit : null;

                  if (limitNum === null) {
                    return (
                      <div key={feature}>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm text-gray-300 capitalize">
                            {feature.replace(/_/g, " ")}
                          </span>
                          <span className="text-sm text-gray-400">Unlimited</span>
                        </div>
                      </div>
                    );
                  }

                  const percentage = Math.min((used / limitNum) * 100, 100);

                  return (
                    <div key={feature}>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-gray-300 capitalize">
                          {feature.replace(/_/g, " ")}
                        </span>
                        <span className="text-sm text-gray-400">
                          {used} / {limitNum}
                        </span>
                      </div>
                      <ProgressBar
                        value={used}
                        max={limitNum}
                        color={
                          percentage > 90
                            ? "red"
                            : percentage > 75
                            ? "yellow"
                            : "green"
                        }
                        showPercentage={false}
                      />
                    </div>
                  );
                }
              )}
            </div>
          )}
        </Card>

        {/* Invoices */}
        <Card
          title="Recent Invoices"
          headerAction={
            can("billing:read") && (
              <Button variant="secondary" size="sm">
                View All Invoices
              </Button>
            )
          }
        >
          {invoices.length === 0 ? (
            <EmptyState
              icon="📄"
              title="No Invoices"
              description="Your recent invoices will appear here"
            />
          ) : (
            <Table
              columns={[
                {
                  key: "invoice_id",
                  label: "Invoice ID",
                  render: (value) => (
                    <span className="font-mono text-xs">
                      {String(value).substring(0, 12)}...
                    </span>
                  ),
                },
                {
                  key: "period_start",
                  label: "Period",
                  render: (_, row: any) =>
                    `${formatDate(row.period_start)} - ${formatDate(row.period_end)}`,
                },
                {
                  key: "total_amount",
                  label: "Amount",
                  align: "right",
                  render: (value) => (
                    <span className="font-semibold">{formatCurrency(Number(value))}</span>
                  ),
                },
                {
                  key: "status",
                  label: "Status",
                  render: (value) => (
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        value === "paid"
                          ? "bg-green-900 text-green-200"
                          : value === "issued"
                          ? "bg-blue-900 text-blue-200"
                          : "bg-red-900 text-red-200"
                      }`}
                    >
                      {String(value).toUpperCase()}
                    </span>
                  ),
                },
                {
                  key: "invoice_id",
                  label: "Action",
                  render: () => (
                    <Button variant="secondary" size="sm">
                      Download
                    </Button>
                  ),
                },
              ]}
              data={invoices}
            />
          )}
        </Card>

        {/* Upgrade/Downgrade CTA */}
        {can("billing:write") && (
          <Card
            title="Plan Options"
            description="Need more capacity or want to switch plans?"
          >
            <div className="flex flex-wrap gap-3">
              <Button variant="primary">Upgrade Plan</Button>
              <Button variant="secondary">Downgrade Plan</Button>
              <Button variant="secondary">Cancel Subscription</Button>
            </div>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};
