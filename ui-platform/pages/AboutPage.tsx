/**
 * About Page — modern SaaS style
 */

import React from "react";
import { InfoNav } from "../components/InfoNav";
import { Footer } from "../components/Footer";

export const AboutPage: React.FC = () => {
  const features = [
    {
      icon: "⚡",
      title: "Fast Setup",
      body: "Go from business requirement to a running structured application in seconds. No lengthy configuration or development cycles.",
    },
    {
      icon: "🔧",
      title: "Customizable Workflows",
      body: "Configurable modules, editable data schemas, and adjustable business rules to fit your exact process.",
    },
    {
      icon: "🏢",
      title: "Business-Focused Structure",
      body: "Templates follow real-world business logic — payroll runs, invoice cycles, lead pipelines — immediately usable by your team.",
    },
    {
      icon: "🔒",
      title: "Full Data Control",
      body: "Your data stays within your own deployed environment. No third-party sharing, no external processing.",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <InfoNav />

      <main className="flex-1">
        {/* Hero */}
        <section className="max-w-4xl mx-auto px-5 pt-16 pb-12 text-center">
          <span className="inline-block px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-600 text-[11px] font-medium tracking-wide mb-5">
            About the platform
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight mb-4">
            About{" "}
            <span className="bg-gradient-to-r from-cyan-500 to-indigo-500 bg-clip-text text-transparent">
              Emergentic AI
            </span>
          </h1>
          <p className="text-sm text-gray-600 leading-relaxed max-w-2xl mx-auto">
            Emergentic AI is an intelligent operating system for modern businesses — generating structured applications for payroll, CRM, invoicing, and operations through AI-assisted templates. Describe your requirement and receive a fully operational application in seconds.
          </p>
        </section>

        {/* Feature grid */}
        <section className="max-w-4xl mx-auto px-5 pb-16">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {features.map((f) => (
              <div
                key={f.title}
                className="bg-white border border-gray-200 hover:border-gray-300 rounded-xl p-5 transition-colors shadow-sm"
              >
                <div className="flex items-center gap-2.5 mb-2.5">
                  <span className="text-lg leading-none">{f.icon}</span>
                  <h3 className="text-sm font-semibold text-gray-900">{f.title}</h3>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA strip */}
        <section className="border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-5 py-8 text-center">
            <p className="text-xs font-semibold text-gray-900 mb-2">Our Mission</p>
            <p className="text-sm text-gray-600 max-w-2xl mx-auto">
              We believe every business should have access to enterprise-grade software. Emergentic AI removes the complexity of building and maintaining business systems, so teams can focus on growth — not infrastructure.
            </p>
          </div>
        </section>

        {/* Team */}
        <section className="bg-gray-50 border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-5 py-12 text-center">
            <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest mb-6">Built by</p>
            <div className="flex flex-wrap justify-center gap-6">
              {[
                { name: "AI Research Team", role: "Platform Intelligence" },
                { name: "Engineering Team", role: "Infrastructure & APIs" },
                { name: "Product Team", role: "UX & Business Templates" },
              ].map((m) => (
                <div key={m.name} className="rounded-xl border border-gray-200 bg-white px-6 py-4 min-w-[160px]">
                  <p className="text-sm font-semibold text-gray-900">{m.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{m.role}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA strip */}
        <section className="border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-5 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-gray-900">Ready to build your first app?</p>
              <p className="text-xs text-gray-600 mt-0.5">
                Open the Orchestrator and describe what you need.
              </p>
            </div>
            <a
              href="/orchestrator"
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors shrink-0"
            >
              Start Building →
            </a>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default AboutPage;
