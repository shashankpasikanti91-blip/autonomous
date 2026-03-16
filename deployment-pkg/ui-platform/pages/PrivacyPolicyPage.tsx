/**
 * Privacy Policy Page — modern SaaS style
 */

import React from "react";
import { InfoNav } from "../components/InfoNav";
import { Footer } from "../components/Footer";

export const PrivacyPolicyPage: React.FC = () => {
  const year = new Date().getFullYear();

  const sections = [
    {
      title: "We do not sell user data",
      body: "All data created, stored, or processed within SRP Autonomous OS remains within your deployed environment. We do not transfer, share, or sell your data to any third party under any circumstances.",
    },
    {
      title: "Data remains within your environment",
      body: "Your deployed environment stores data in the infrastructure you control. SRP Autonomous OS does not host or mirror your business data on external servers beyond what is explicitly configured in your deployment.",
    },
    {
      title: "Minimal data collection",
      body: "SRP Autonomous OS collects only the minimum data necessary to operate the platform — specifically, authentication credentials and usage metadata required for session management. No personal profiling or behavioural tracking is performed.",
    },
    {
      title: "Secure authentication practices",
      body: "Access to the platform is protected by secure authentication. Credentials are stored using industry-standard hashing. Sessions are token-based with configurable expiry. We recommend strong password policies for all user accounts.",
    },
    {
      title: "Third-party services",
      body: "Where third-party integrations are configured by the user, data flows are governed by the respective third-party privacy policies. SRP Autonomous OS does not control those services.",
    },
    {
      title: "Policy updates",
      body: "This privacy policy may be updated periodically to reflect changes in the platform or applicable regulations. Users will be notified of material changes through platform announcements.",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <InfoNav />

      <main className="flex-1 max-w-3xl mx-auto px-5 pt-14 pb-16 w-full">
        <div className="mb-8">
          <h1 className="text-xl font-bold text-gray-900 mb-1">Privacy Policy</h1>
          <p className="text-xs text-gray-600">Last updated: January {year}</p>
        </div>

        <p className="text-xs text-gray-600 leading-relaxed mb-8 pb-8 border-b border-gray-200">
          SRP Autonomous OS is committed to protecting the privacy of its users and the
          confidentiality of business data processed through the platform.
        </p>

        <div className="space-y-6">
          {sections.map((s, i) => (
            <div key={i} className="group">
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

export default PrivacyPolicyPage;
