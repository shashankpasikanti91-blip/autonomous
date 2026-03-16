/**
 * Billing Service Layer
 * Handles subscriptions, invoices, and billing management
 */

import {
  Subscription,
  Invoice,
  SubscriptionPlan,
  BillingEvents,
  PaginatedResponse,
} from "../types/index";

class BillingService {
  private _demoSubscription(tenantId?: string): Subscription {
    return {
      subscription_id: "sub_demo",
      tenant_id: tenantId || "demo-tenant",
      plan: "starter",
      billing_cycle_start: "2026-01-01T00:00:00Z",
      billing_cycle_end: "2026-01-31T23:59:59Z",
      auto_renew: true,
      status: "active",
      current_period_usage: {},
    } as Subscription;
  }

  async getSubscription(_tenantId?: string): Promise<Subscription> {
    return this._demoSubscription(_tenantId);
  }

  async upgradePlan(tenantId: string, newPlan: SubscriptionPlan): Promise<Subscription> {
    return { ...this._demoSubscription(tenantId), plan: newPlan } as Subscription;
  }

  async downgradePlan(tenantId: string, newPlan: SubscriptionPlan): Promise<Subscription> {
    return { ...this._demoSubscription(tenantId), plan: newPlan } as Subscription;
  }

  async cancelSubscription(tenantId: string): Promise<Subscription> {
    return { ...this._demoSubscription(tenantId), status: "cancelled" } as Subscription;
  }

  async getInvoices(
    _tenantId?: string,
    limit = 50,
    offset = 0
  ): Promise<PaginatedResponse<Invoice>> {
    return { items: [], total: 0, limit, offset };
  }

  async getInvoice(invoiceId: string): Promise<Invoice> {
    return { invoice_id: invoiceId, tenant_id: "demo-tenant", amount: 0, status: "paid", created_at: "2026-01-01T00:00:00Z" } as unknown as Invoice;
  }

  async downloadInvoice(_invoiceId: string): Promise<Blob> {
    return new Blob([""], { type: "application/pdf" });
  }

  async getBillingEvents(
    _tenantId?: string,
    _startDate?: string,
    _endDate?: string
  ): Promise<BillingEvents> {
    return { events: [], total: 0 } as unknown as BillingEvents;
  }

  async getUsageData(
    _tenantId?: string,
    _period: "day" | "month" | "year" = "month"
  ): Promise<Record<string, unknown>> {
    return { api_calls: 0, storage_gb: 0, executions: 0 };
  }

  async setPaymentMethod(
    _tenantId: string,
    paymentMethodData: Record<string, unknown>
  ): Promise<Record<string, unknown>> {
    return { success: true, ...paymentMethodData };
  }

  async getEstimatedCost(
    _tenantId: string,
    _plan: SubscriptionPlan
  ): Promise<{ estimated_monthly: number; estimated_annual: number }> {
    return { estimated_monthly: 0, estimated_annual: 0 };
  }
}

export const billingService = new BillingService();
