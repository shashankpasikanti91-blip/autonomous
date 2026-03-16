/**
 * Shared top navigation bar used on all public info pages.
 * Keeps all marketing pages consistent.
 */

import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export const InfoNav: React.FC = () => {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { label: "About",        to: "/about" },
    { label: "Pricing",      to: "/pricing" },
    { label: "How It Works", to: "/how-it-works" },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-5xl mx-auto px-5 h-14 flex items-center justify-between">
        {/* Brand */}
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2.5 group"
        >
          <span className="text-lg leading-none">⚡</span>
          <span className="text-sm font-bold text-gray-900 group-hover:text-cyan-600 transition-colors leading-none">
            Emergentic AI
          </span>
        </button>

        {/* Desktop links */}
        <nav className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <button
              key={l.to}
              onClick={() => navigate(l.to)}
              className={`px-3 py-1.5 rounded-md text-xs transition-colors ${
                pathname === l.to
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              {l.label}
            </button>
          ))}
          <button
            onClick={() => navigate("/dashboard")}
            className="ml-3 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
          >
            Open App →
          </button>
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-gray-600 hover:text-gray-900 p-1"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
            {mobileOpen ? (
              <>
                <line x1="3" y1="3" x2="15" y2="15" />
                <line x1="15" y1="3" x2="3" y2="15" />
              </>
            ) : (
              <>
                <line x1="2" y1="5" x2="16" y2="5" />
                <line x1="2" y1="9" x2="16" y2="9" />
                <line x1="2" y1="13" x2="16" y2="13" />
              </>
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-5 py-3 space-y-1">
          {links.map((l) => (
            <button
              key={l.to}
              onClick={() => { navigate(l.to); setMobileOpen(false); }}
              className="block w-full text-left px-3 py-2 rounded-md text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              {l.label}
            </button>
          ))}
          <button
            onClick={() => { navigate("/dashboard"); setMobileOpen(false); }}
            className="block w-full text-left px-3 py-2 rounded-md text-sm text-blue-600 hover:text-blue-700 transition-colors"
          >
            Open App →
          </button>
        </div>
      )}
    </header>
  );
};

export default InfoNav;
