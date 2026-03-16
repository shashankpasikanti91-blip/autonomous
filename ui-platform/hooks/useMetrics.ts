/**
 * useMetrics Hook
 * Manages real-time metrics with polling support
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { TenantMetrics, PlatformHealth, metricsService } from "../services";

export interface UseMetricsOptions {
  pollInterval?: number; // milliseconds, 0 to disable
  tenantId?: string;
  autoLoad?: boolean;
}

export interface UseMetricsResult {
  tenantMetrics: TenantMetrics | null;
  platformHealth: PlatformHealth | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  startPolling: (interval: number) => void;
  stopPolling: () => void;
}

export function useMetrics(options: UseMetricsOptions = {}): UseMetricsResult {
  const {
    pollInterval = 30000, // 30 seconds default
    tenantId,
    autoLoad = true,
  } = options;

  const [tenantMetrics, setTenantMetrics] = useState<TenantMetrics | null>(
    null
  );
  const [platformHealth, setPlatformHealth] = useState<PlatformHealth | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollIntervalRef = useRef<number>(pollInterval);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [metrics, health] = await Promise.all([
        metricsService.getTenantMetrics(tenantId),
        metricsService.getPlatformHealth(),
      ]);

      setTenantMetrics(metrics);
      setPlatformHealth(health);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch metrics";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [tenantId]);

  const startPolling = useCallback((interval: number) => {
    pollIntervalRef.current = interval;

    // Clear existing interval
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Start new interval
    const intervalId = setInterval(() => {
      refresh();
    }, interval);

    pollingIntervalRef.current = intervalId;
  }, [refresh]);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  // Auto-load and setup polling on mount
  useEffect(() => {
    if (autoLoad) {
      refresh();

      if (pollInterval > 0) {
        startPolling(pollInterval);
      }
    }

    return () => {
      stopPolling();
    };
  }, [autoLoad, pollInterval, refresh, startPolling, stopPolling]);

  return {
    tenantMetrics,
    platformHealth,
    isLoading,
    error,
    refresh,
    startPolling,
    stopPolling,
  };
}
