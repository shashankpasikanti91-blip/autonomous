/**
 * Terms of Service Page — modern SaaS style
 */

import React from "react";
import { InfoNav } from "../components/InfoNav";
import { Footer } from "../components/Footer";

export const TermsOfServicePage: React.FC = () => {
  const year = new Date().getFullYear();

  const sections = [
    {
      title: "Platform provides structured application generation",
      body: "SRP Autonomous OS provides structured application generation services. The platform generates business applications based on user descriptions and pre-defined templates for internal business use.",
    },
    {
      title: "Users are responsible for business compliance",
      body: "Users are responsible for ensuring that their use of generated applications complies with all applicable laws, regulations, and business compliance requirements in their jurisdiction — including employment law, tax regulations, and data protection requirements.",
    },
    {
      title: "Verify compliance before operational use",
      body: "Generated payroll, invoicing, CRM, and other business systems are structural tools. SRP Autonomous OS does not certify that any generated application meets specific regulatory requirements. Validate generated systems against your compliance obligations.",
    },
    {
      title: "No liability for misuse",
      body: "SRP Autonomous OS shall not be liable for any direct, indirect, incidental, or consequential damages arising from misuse of the platform, reliance on generated applications for regulated business activities, or failure to comply with applicable laws.",
    },
    {
      title: "Intellectual property",
      body: "Business templates, AI models, and platform infrastructure are the intellectual property of SRP Autonomous OS. Applications generated for users remain the property of the respective user organisation.",
    },
    {
      title: "Terms subject to updates",
      body: "These terms are subject to periodic updates. Continued use of the platform following any update constitutes acceptance of the revised terms. Material changes will be communicated through platform notifications.",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <InfoNav />

      <main className="flex-1 max-w-3xl mx-auto px-5 pt-14 pb-16 w-full">
        <div className="mb-8">
          <h1 className="text-xl font-bold text-gray-900 mb-1">Terms of Service</h1>
          <p className="text-xs text-gray-600">Last updated: January {year}</p>
        </div>

        <p className="text-xs text-gray-600 leading-relaxed mb-8 pb-8 border-b border-gray-200">
          By accessing or using SRP Autonomous OS, you agree to be bound by the following terms
          and conditions. Please read them carefully before using the platform.
        </p>

        <div className="space-y-6">
          {sections.map((s, i) => (
            <div key={i}>
              <div className="flex items-start gap-4">
                <span className="shrink-0 w-5 h-5 rounded-md bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 text-[9px] font-bold mt-0.5">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-1.5">{s.title}</h3>
                  <p className="text-xs text-gray-600 leading-relaxed">{s.body}</p>
                </div>
              </div>
              {i < sections.length - 1 && (
                <div className="mt-6 ml-9 border-t border-gray-200" />
              )}
            </div>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default TermsOfServicePage;
