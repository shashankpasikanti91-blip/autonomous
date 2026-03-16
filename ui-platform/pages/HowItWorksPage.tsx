/**
 * How It Works Page — modern SaaS style
 */

import React from "react";
import { InfoNav } from "../components/InfoNav";
import { Footer } from "../components/Footer";

export const HowItWorksPage: React.FC = () => {
  const steps = [
    {
      number: "01",
      title: "Describe Your Requirement",
      body: "Type a plain-language description of the business system you need — such as 'Build a payroll system for 50 employees with attendance tracking'. No technical specification required.",
      tag: "Natural Language Input",
    },
    {
      number: "02",
      title: "System Generates Structured Application",
      body: "Emergentic AI analyses your requirement, selects the matching business template, and scaffolds a fully structured application — complete with database tables, modules, sidebar navigation, and summary cards.",
      tag: "AI-Powered Generation",
    },
    {
      number: "03",
      title: "Manage and Operate Instantly",
      body: "Your application is immediately ready to use. Add employees, generate payroll runs, create invoices, or manage leads — all from a structured interface purpose-built for your business process.",
      tag: "Operational from Day 0",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <InfoNav />

      <main className="flex-1">
        {/* Hero */}
        <section className="max-w-4xl mx-auto px-5 pt-16 pb-12 text-center">
          <span className="inline-block px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-600 text-[11px] font-medium tracking-wide mb-5">
            The process
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight mb-4">
            From{" "}
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              idea to running app
            </span>{" "}
            in three steps
          </h1>
          <p className="text-sm text-gray-600 leading-relaxed max-w-xl mx-auto">
            No development team, no lengthy specification. Just describe what your business
            needs — and Emergentic AI handles the rest.
          </p>
        </section>

        {/* Steps */}
        <section className="max-w-3xl mx-auto px-5 pb-16 space-y-4">
          {steps.map((step, i) => (
            <div
              key={i}
              className="relative bg-white border border-gray-200 hover:border-gray-300 rounded-xl p-6 flex gap-5 transition-colors shadow-sm"
            >
              {/* Number */}
              <div className="shrink-0 w-10 h-10 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center">
                <span className="text-blue-600 text-xs font-bold font-mono">{step.number}</span>
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  <h3 className="text-sm font-semibold text-gray-900">{step.title}</h3>
                  <span className="px-2 py-0.5 rounded-full bg-gray-100 border border-gray-200 text-[10px] text-gray-500">
                    {step.tag}
                  </span>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">{step.body}</p>
              </div>
            </div>
          ))}
        </section>

        {/* CTA */}
        <section className="border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-5 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-gray-900">Try it yourself in under a minute.</p>
              <p className="text-xs text-gray-600 mt-0.5">Open the Orchestrator and type your requirement.</p>
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

export default HowItWorksPage;
