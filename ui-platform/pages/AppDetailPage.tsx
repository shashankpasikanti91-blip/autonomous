/**
 * App Detail Page  —  /apps/:appId
 *
 * Routing strategy:
 *
 *   app.blueprint present  →  <TemplateRenderer blueprint={…} app={…} />
 *      Renders: sidebar nav, summary cards, CRUD modules, action modules,
 *               run history — all driven by the blueprint JSON.
 *
 *   no blueprint (custom)  →  <GenericApp app={…} />
 *      Renders: header, app info, module tabs, run console, run history.
 */

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { MainLayout } from "../components/layouts/MainLayout";
import { Loading, ErrorAlert } from "../components/common/UIComponents";
import { appService } from "../services";
import type { App } from "../types";
import { TemplateRenderer } from "../src/templates/TemplateRenderer";
import type { Blueprint } from "../src/templates/TemplateRenderer";
import { GenericApp } from "../src/templates/GenericApp";

// ─── Enriched App type ────────────────────────────────────────────────────────

type RichApp = App & {
  app_type?: string | null;
  description?: string;
  blueprint?: Blueprint | string | null;
  [key: string]: unknown;
};

// ─── Component ────────────────────────────────────────────────────────────────

export const AppDetailPage: React.FC = () => {
  const { appId } = useParams<{ appId: string }>();

  const [app, setApp]       = useState<RichApp | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);

  useEffect(() => {
    if (!appId) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const found = await appService.getApp(appId);
        if (!cancelled) setApp(found as RichApp);
      } catch {
        if (!cancelled) setError("App not found");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [appId]);

  // ── Loading guard ──────────────────────────────────────────────────────────
  if (loading) return (
    <MainLayout>
      <div className="flex items-center justify-center h-64"><Loading /></div>
    </MainLayout>
  );

  // ── Error guard ────────────────────────────────────────────────────────────
  if (error || !app) return (
    <MainLayout>
      <div className="p-6"><ErrorAlert message={error || "App not found"} /></div>
    </MainLayout>
  );

  // ── Blueprint routing ──────────────────────────────────────────────────────
  // blueprint may arrive as a parsed object or as a JSON string from the API
  let blueprint: Blueprint | null = null;
  if (app.blueprint) {
    if (typeof app.blueprint === "string") {
      try { blueprint = JSON.parse(app.blueprint) as Blueprint; } catch { /* malformed — fall through to GenericApp */ }
    } else {
      blueprint = app.blueprint as Blueprint;
    }
  }

  if (blueprint) {
    return <TemplateRenderer blueprint={blueprint} app={app} />;
  }

  return <GenericApp app={app} />;
};


export default AppDetailPage;

