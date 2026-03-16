/**
 * Help & Documentation Page
 * API reference quick links, FAQ, support
 */

import React, { useState } from "react";
import { MainLayout } from "../components/layouts/MainLayout";
import { Card } from "../components/common/UIComponents";

const FAQ = [
  {
    q: "How do I trigger a workflow?",
    a: "POST to /workflows/{workflow_id}/execute with a JSON body containing your input data. You can also use the n8n webhook endpoints at /n8n/webhook/{trigger_name}.",
  },
  {
    q: "How does authentication work?",
    a: "The platform uses Firebase Auth (currently in mock mode for local development). POST to /auth/login with { email, password } to receive a token, then include it as a Bearer token in subsequent requests.",
  },
  {
    q: "How do I onboard a new employee?",
    a: "POST to /onboarding/employee with fields: employee_id, employee_name, employee_email, department, start_date. The system will trigger the onboarding workflow automatically.",
  },
  {
    q: "Where is the API documentation?",
    a: "The full interactive API docs (Swagger UI) are available at http://localhost:8000/docs when the backend is running.",
  },
  {
    q: "How do I check the platform health?",
    a: "GET http://localhost:8000/health — returns status, version, and timestamp. The /metrics endpoint returns detailed system statistics.",
  },
  {
    q: "What is mock mode?",
    a: "Firebase, external APIs (Google Calendar, HubSpot, etc.) are in mock/stub mode for local development. They return simulated data without requiring real API keys.",
  },
];

export const HelpPage: React.FC = () => {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <MainLayout title="Help & Documentation">
      <div className="p-6 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white">Help & Documentation</h2>
          <p className="text-gray-400 mt-1">API reference, guides, and frequently asked questions</p>
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              icon: "📖",
              title: "API Docs (Swagger)",
              desc: "Full interactive API reference",
              href: "http://localhost:8000/docs",
              color: "from-blue-600 to-blue-800",
            },
            {
              icon: "🔍",
              title: "API Redoc",
              desc: "Clean readable API reference",
              href: "http://localhost:8000/redoc",
              color: "from-purple-600 to-purple-800",
            },
            {
              icon: "❤️",
              title: "Health Check",
              desc: "Backend status & version",
              href: "http://localhost:8000/health",
              color: "from-green-600 to-green-800",
            },
          ].map((item) => (
            <a
              key={item.title}
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className={`bg-gradient-to-br ${item.color} rounded-lg p-5 hover:opacity-90 transition-opacity`}
            >
              <div className="text-3xl mb-2">{item.icon}</div>
              <h3 className="font-semibold text-white">{item.title}</h3>
              <p className="text-sm text-gray-200 mt-1">{item.desc}</p>
            </a>
          ))}
        </div>

        {/* API Endpoints Reference */}
        <Card title="Key API Endpoints">
          <div className="space-y-2 text-sm font-mono">
            {[
              { method: "GET",  path: "/health",                     desc: "Platform health check" },
              { method: "GET",  path: "/info",                       desc: "Platform info & version" },
              { method: "POST", path: "/auth/login",                 desc: "Authenticate user" },
              { method: "GET",  path: "/agents",                     desc: "List all AI agents" },
              { method: "POST", path: "/workflows",                  desc: "Create workflow" },
              { method: "POST", path: "/workflows/{id}/execute",     desc: "Execute workflow" },
              { method: "POST", path: "/onboarding/employee",        desc: "Trigger employee onboarding" },
              { method: "POST", path: "/recruitment/generate-jd",    desc: "Generate job description" },
              { method: "POST", path: "/payroll/process",            desc: "Process payroll" },
              { method: "POST", path: "/invoice/generate",           desc: "Generate invoice" },
              { method: "POST", path: "/meetings/schedule",          desc: "Schedule meeting" },
              { method: "POST", path: "/sales/generate-lead",        desc: "Generate sales lead" },
              { method: "POST", path: "/n8n/webhook/{trigger}",      desc: "Trigger n8n webhook" },
              { method: "POST", path: "/data/{collection}/{doc_id}", desc: "Store data (Firestore)" },
              { method: "GET",  path: "/data/{collection}/{doc_id}", desc: "Retrieve data" },
            ].map((ep) => (
              <div key={ep.path} className="flex items-start gap-3 py-1.5 border-b border-gray-700">
                <span
                  className={`w-14 text-center px-1 py-0.5 rounded text-xs font-bold shrink-0 ${
                    ep.method === "GET"
                      ? "bg-green-900 text-green-300"
                      : "bg-blue-900 text-blue-300"
                  }`}
                >
                  {ep.method}
                </span>
                <span className="text-blue-400 w-64 shrink-0">{ep.path}</span>
                <span className="text-gray-400">{ep.desc}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* FAQ */}
        <Card title="Frequently Asked Questions">
          <div className="space-y-2">
            {FAQ.map((item, i) => (
              <div key={i} className="border border-gray-700 rounded-lg overflow-hidden">
                <button
                  className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-700 transition-colors"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                >
                  <span className="text-sm font-medium text-white">{item.q}</span>
                  <span className="text-gray-400 ml-4">{openFaq === i ? "▲" : "▼"}</span>
                </button>
                {openFaq === i && (
                  <div className="px-4 pb-3 text-sm text-gray-300 bg-gray-800 border-t border-gray-700">
                    {item.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* Support */}
        <Card title="Support">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 bg-gray-700 rounded-lg p-4">
              <div className="text-2xl mb-2">📧</div>
              <h4 className="font-semibold text-white">Email Support</h4>
              <p className="text-sm text-gray-400 mt-1">support@srpautonomous.com</p>
            </div>
            <div className="flex-1 bg-gray-700 rounded-lg p-4">
              <div className="text-2xl mb-2">💬</div>
              <h4 className="font-semibold text-white">Documentation</h4>
              <p className="text-sm text-gray-400 mt-1">See README.md in the project root for full setup guide</p>
            </div>
            <div className="flex-1 bg-gray-700 rounded-lg p-4">
              <div className="text-2xl mb-2">🐛</div>
              <h4 className="font-semibold text-white">Backend Version</h4>
              <p className="text-sm text-gray-400 mt-1">v2.0.0 — FastAPI + Python 3.14</p>
            </div>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
};

export { HelpPage as default };
