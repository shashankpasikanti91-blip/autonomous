/**
 * Settings Page
 * Tenant configuration, API keys, integrations, notifications
 */

import React, { useState } from "react";
import { MainLayout } from "../components/layouts/MainLayout";
import { Card, Button } from "../components/common/UIComponents";

export const SettingsPage: React.FC = () => {
  const userEmail = localStorage.getItem("user_email") || "admin@demo.com";
  const userName = localStorage.getItem("user_name") || "Admin";

  const [activeTab, setActiveTab] = useState<"general" | "api" | "notifications" | "integrations">("general");
  const [saved, setSaved] = useState(false);

  const [generalForm, setGeneralForm] = useState({
    orgName: "SRP Autonomous OS",
    timezone: "UTC",
    language: "en",
  });

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const tabs = [
    { key: "general", label: "⚙️ General" },
    { key: "api", label: "🔑 API Keys" },
    { key: "notifications", label: "🔔 Notifications" },
    { key: "integrations", label: "🔗 Integrations" },
  ] as const;

  return (
    <MainLayout title="Settings">
      <div className="p-6 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white">Settings</h2>
          <p className="text-gray-400 mt-1">Manage your platform configuration</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-700">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === t.key
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-gray-400 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* General */}
        {activeTab === "general" && (
          <Card title="General Settings">
            <div className="space-y-4 max-w-lg">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Organization Name</label>
                <input
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                  value={generalForm.orgName}
                  onChange={(e) => setGeneralForm({ ...generalForm, orgName: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Account Email</label>
                <input
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-gray-400 cursor-not-allowed"
                  value={userEmail}
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Display Name</label>
                <input
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                  value={userName}
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Timezone</label>
                <select
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
                  value={generalForm.timezone}
                  onChange={(e) => setGeneralForm({ ...generalForm, timezone: e.target.value })}
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time (US)</option>
                  <option value="America/Los_Angeles">Pacific Time (US)</option>
                  <option value="Europe/London">London</option>
                  <option value="Asia/Kuala_Lumpur">Kuala Lumpur (MYT)</option>
                  <option value="Asia/Singapore">Singapore (SGT)</option>
                </select>
              </div>
              <Button variant="primary" onClick={handleSave}>
                {saved ? "✓ Saved!" : "Save Changes"}
              </Button>
            </div>
          </Card>
        )}

        {/* API Keys */}
        {activeTab === "api" && (
          <Card title="API Keys">
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">Use these keys to connect your services to the platform API at <code className="text-blue-400">http://localhost:8000</code></p>
              <div className="bg-gray-900 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">Production API Key</p>
                    <p className="text-xs text-gray-400 font-mono mt-1">srp_prod_••••••••••••••••••••••••</p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={() => { navigator.clipboard.writeText("srp_prod_demo_key_1234567890") }}>
                    Copy
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">Development API Key</p>
                    <p className="text-xs text-gray-400 font-mono mt-1">srp_dev_••••••••••••••••••••••••</p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={() => { navigator.clipboard.writeText("srp_dev_demo_key_0987654321") }}>
                    Copy
                  </Button>
                </div>
              </div>
              <Button variant="secondary" onClick={handleSave}>+ Generate New Key</Button>
            </div>
          </Card>
        )}

        {/* Notifications */}
        {activeTab === "notifications" && (
          <Card title="Notification Preferences">
            <div className="space-y-3 max-w-lg">
              {[
                { label: "Workflow completion alerts", desc: "Notify when a workflow finishes" },
                { label: "Error & failure alerts", desc: "Notify on workflow or agent failure" },
                { label: "Billing threshold alerts", desc: "Notify at 80% and 100% quota usage" },
                { label: "New user invitations", desc: "Notify when a user joins your tenant" },
                { label: "Weekly usage report", desc: "Summary email every Monday" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-gray-700">
                  <div>
                    <p className="text-sm text-white">{item.label}</p>
                    <p className="text-xs text-gray-400">{item.desc}</p>
                  </div>
                  <input type="checkbox" defaultChecked className="w-4 h-4 accent-blue-500" />
                </div>
              ))}
              <Button variant="primary" onClick={handleSave}>
                {saved ? "✓ Saved!" : "Save Preferences"}
              </Button>
            </div>
          </Card>
        )}

        {/* Integrations */}
        {activeTab === "integrations" && (
          <Card title="Integrations">
            <div className="space-y-3">
              {[
                { name: "n8n Webhooks", status: "connected", icon: "🔗", desc: "Workflow automation via n8n" },
                { name: "OpenAI / LLM", status: "configure", icon: "🤖", desc: "AI model API connection" },
                { name: "Google Calendar", status: "configure", icon: "📅", desc: "Meeting scheduling integration" },
                { name: "HubSpot CRM", status: "configure", icon: "📊", desc: "Sales lead management" },
                { name: "Firebase", status: "configure", icon: "🔥", desc: "Database & authentication (mock mode)" },
                { name: "Slack", status: "configure", icon: "💬", desc: "Team notification channel" },
              ].map((item) => (
                <div key={item.name} className="flex items-center justify-between py-3 border-b border-gray-700">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{item.icon}</span>
                    <div>
                      <p className="text-sm font-medium text-white">{item.name}</p>
                      <p className="text-xs text-gray-400">{item.desc}</p>
                    </div>
                  </div>
                  <span
                    className={`px-2 py-1 rounded text-xs font-semibold ${
                      item.status === "connected"
                        ? "bg-green-900 text-green-300"
                        : "bg-gray-700 text-gray-300"
                    }`}
                  >
                    {item.status === "connected" ? "✓ Connected" : "Configure"}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};

export { SettingsPage as default };
