/**
 * Main Layout Component
 * Primary layout with header, sidebar, and footer
 */

import React, { useState } from "react";
import { useAuth, usePermission } from "../../hooks";
import { APP_NAME, APP_TAGLINE } from "../../utils";
import { Footer } from "../Footer";

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  title,
  breadcrumbs,
}) => {
  const { user, tenant, logout } = useAuth();
  const { isAdmin } = usePermission();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navigationItems = [
    { label: "Dashboard", href: "/dashboard", icon: "📊" },
    { label: "Apps", href: "/apps", icon: "⚙️" },
    { label: "Orchestrator", href: "/orchestrator", icon: "🧠" },
    { label: "Billing", href: "/billing", icon: "💳" },
    { label: "Metrics", href: "/metrics", icon: "📈" },
    ...(isAdmin
      ? [
          { label: "Users", href: "/users", icon: "👥" },
          { label: "Settings", href: "/settings", icon: "⚙️" },
        ]
      : []),
  ];

  const infoNavItems = [
    { label: "About", href: "/about" },
    { label: "Pricing", href: "/pricing" },
    { label: "How It Works", href: "/how-it-works" },
  ];

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-64" : "w-20"
        } bg-gray-800 border-r border-gray-700 transition-all duration-300`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                🚀
              </div>
              {sidebarOpen && (
                <div>
                  <h1 className="font-bold text-sm">{APP_NAME}</h1>
                  <p className="text-xs text-gray-400">{APP_TAGLINE}</p>
                </div>
              )}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-2">
            {navigationItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                <span className="text-lg">{item.icon}</span>
                {sidebarOpen && <span className="text-sm">{item.label}</span>}
              </a>
            ))}
          </nav>

          {/* Info nav links */}
          {sidebarOpen && (
            <div className="px-4 py-2 border-t border-gray-700">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Platform</p>
              {infoNavItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="flex items-center px-2 py-1.5 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-700 transition-colors"
                >
                  {item.label}
                </a>
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="p-4 border-t border-gray-700 space-y-2">
            <a
              href="/help"
              className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <span className="text-lg">❓</span>
              {sidebarOpen && <span className="text-sm">Help</span>}
            </a>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="w-full flex items-center justify-center px-3 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <span className="text-lg">{sidebarOpen ? "◀" : "▶"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              {breadcrumbs && (
                <div className="text-sm text-gray-400 mb-2">
                  {breadcrumbs.map((item, index) => (
                    <span key={index}>
                      {item.href ? (
                        <a href={item.href} className="hover:text-white">
                          {item.label}
                        </a>
                      ) : (
                        item.label
                      )}
                      {index < breadcrumbs.length - 1 && " / "}
                    </span>
                  ))}
                </div>
              )}
              {title && <h1 className="text-2xl font-bold">{title}</h1>}
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium">{user?.email}</p>
                <p className="text-xs text-gray-400">{tenant?.organization_name}</p>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-gray-900 p-6">
          {children}
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
};
