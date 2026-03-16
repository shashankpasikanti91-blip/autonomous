/**
 * useTenant Hook
 * Manages tenant context and operations
 */

import {
  useState,
  useEffect,
  useCallback,
  useContext,
  createContext,
} from "react";
import { Tenant, TenantQuota, tenantService } from "../services";

export interface TenantContextType {
  tenant: Tenant | null;
  quota: TenantQuota | null;
  isLoading: boolean;
  error: string | null;
  refreshTenant: () => Promise<void>;
  refreshQuota: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export function useTenant(): TenantContextType {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error("useTenant must be used within TenantProvider");
  }
  return context;
}

export function useTenantState() {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [quota, setQuota] = useState<TenantQuota | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshTenant = useCallback(async () => {
    setIsLoading(true);
    try {
      const currentTenant = await tenantService.getCurrentTenant();
      setTenant(currentTenant);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch tenant";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshQuota = useCallback(async () => {
    try {
      const currentQuota = await tenantService.getQuota();
      setQuota(currentQuota);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch quota";
      setError(message);
    }
  }, []);

  // Load tenant and quota on mount
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([refreshTenant(), refreshQuota()]);
    };

    loadData();
  }, [refreshTenant, refreshQuota]);

  return {
    tenant,
    quota,
    isLoading,
    error,
    refreshTenant,
    refreshQuota,
  };
}

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const tenantState = useTenantState();

  return (
    <TenantContext.Provider value={tenantState}>{children}</TenantContext.Provider>
  );
};
