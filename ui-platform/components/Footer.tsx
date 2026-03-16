/**
 * Global Footer Component
 * Appears on all platform pages via MainLayout.
 */

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

interface FooterColumnProps {
  heading: string;
  links: Array<{ label: string; to: string }>;
}

const FooterColumn: React.FC<FooterColumnProps> = ({ heading, links }) => {
  const navigate = useNavigate();
  return (
    <div className="min-w-[120px]">
      <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest mb-3">
        {heading}
      </p>
      <ul className="space-y-2">
        {links.map((l) => (
          <li key={l.to}>
            <button
              onClick={() => navigate(l.to)}
              className="text-xs text-gray-600 hover:text-gray-900 transition-colors text-left"
            >
              {l.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export const Footer: React.FC = () => {
  const year = new Date().getFullYear();
  const [expanded, setExpanded] = useState(false);

  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      {/* Toggle bar — always visible */}
      <div
        className="flex items-center justify-between px-6 py-2 cursor-pointer hover:bg-gray-100 transition-colors select-none"
        onClick={() => setExpanded((v) => !v)}
        title={expanded ? "Collapse footer" : "Expand footer"}
      >
        <p className="text-[11px] text-gray-400">
          © {year} Emergentic AI. All rights reserved. &nbsp;·&nbsp; Powered by AI-driven automation
        </p>
        <button
          className="ml-4 flex items-center gap-1 text-[11px] text-gray-400 hover:text-gray-700 transition-colors whitespace-nowrap"
          onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v); }}
        >
          {expanded ? "▼ Hide" : "▲ Show"}
        </button>
      </div>

      {/* Expandable content */}
      {expanded && (
        <div className="max-w-5xl mx-auto px-6 pb-8 pt-4">
          <div className="flex flex-col gap-8 md:flex-row md:justify-between">
            {/* Brand */}
            <div className="max-w-[220px]">
              <div className="flex items-center gap-2 mb-2">
              <span className="text-base leading-none">⚡</span>
              <span className="text-sm font-bold text-gray-900">Emergentic AI</span>
            </div>
            <p className="text-[11px] text-gray-500 leading-relaxed">
              Build intelligent business systems through AI-driven automation.
            </p>
            </div>

            {/* Columns */}
            <div className="flex flex-wrap gap-x-12 gap-y-8">
              <FooterColumn
                heading="Product"
                links={[
                  { label: "Build", to: "/orchestrator" },
                  { label: "Pricing", to: "/pricing" },
                ]}
              />
              <FooterColumn
                heading="Company"
                links={[
                  { label: "About", to: "/about" },
                  { label: "How It Works", to: "/how-it-works" },
                ]}
              />
              <FooterColumn
                heading="Legal"
                links={[
                  { label: "Privacy Policy", to: "/privacy-policy" },
                  { label: "Terms of Service", to: "/terms-of-service" },
                ]}
              />
            </div>
          </div>
        </div>
      )}
    </footer>
  );
};

export default Footer;
