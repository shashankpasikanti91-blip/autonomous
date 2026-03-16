/**
 * Main App Component
 * Application entry point with routing and providers
 */

import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { TenantProvider } from "./hooks/useTenant";

// Pages
import {
  TenantDashboard,
  BillingDashboard,
  ObservabilityDashboard,
  AppManagementConsole,
  RBACManagement,
  PlatformAdminConsole,
  SettingsPage,
  HelpPage,
  AppDetailPage,
  OrchestratorPage,
  AboutPage,
  HowItWorksPage,
  PricingPage,
  PrivacyPolicyPage,
  TermsOfServicePage,
} from "./pages";

// Style
import "./styles/globals.css";

// Login Page
const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setError('Please enter your email and password.')
      return
    }
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch {
      setError('Login failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white">
      <div className="absolute inset-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 20% 20%, #22d3ee 0, transparent 30%), radial-gradient(circle at 80% 0%, #6366f1 0, transparent 25%), radial-gradient(circle at 30% 80%, #22c55e 0, transparent 25%)" }} />

      <header className="relative z-10 px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/10 border border-white/10 flex items-center justify-center text-white font-bold text-sm">HR</div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-white/60">Multi-Tenant</p>
            <p className="text-sm font-semibold">HR Autonomous OS</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-white/70">
          <a className="hover:text-white" href="/about">About</a>
          <a className="hover:text-white" href="/pricing">Pricing</a>
          <a className="hover:text-white" href="/how-it-works">How it works</a>
        </div>
      </header>

      <main className="relative z-10 px-6 sm:px-10 pb-14">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Hero copy */}
          <div className="space-y-5">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/10 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">HR + Payroll + Compliance</span>
            <h1 className="text-3xl sm:text-4xl font-semibold leading-tight">
              Build and run secure HR stacks for every tenant—without touching other projects.
            </h1>
            <p className="text-sm text-white/70 max-w-xl">
              Onboard clients, provision isolated databases, and manage payroll/people ops from one control plane.
              Subdomain or custom domain per tenant, zero cross-talk.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-left">
              {[{ label: "Provisioning", value: "< 60s" }, { label: "Templates", value: "7 industries" }, { label: "Data Isolation", value: "Per-tenant DB" }].map((item) => (
                <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                  <p className="text-xs text-white/60">{item.label}</p>
                  <p className="text-lg font-semibold">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Auth card */}
          <div className="bg-white text-slate-900 rounded-2xl shadow-2xl border border-white/10 p-8 relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: "linear-gradient(120deg, rgba(99,102,241,0.06), rgba(45,212,191,0.08))" }} />
            <div className="relative space-y-6">
              <div>
                <p className="text-xs font-semibold text-indigo-600 uppercase tracking-[0.2em]">Tenant access</p>
                <h2 className="text-2xl font-semibold mt-1">Sign in to your workspace</h2>
                <p className="text-sm text-slate-600">Enter your email and password. Tenants are resolved by subdomain or custom domain automatically.</p>
              </div>

              {error && (
                <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-red-600 text-xs">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-800 font-semibold mb-1">Email</label>
                  <input
                    type="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-800 font-semibold mb-1">Password</label>
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none text-sm"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-500 text-white text-sm font-semibold shadow-lg shadow-indigo-500/25 hover:translate-y-[-1px] transition"
                >
                  Access Workspace →
                </button>
              </form>

              <div className="text-[11px] text-slate-500">
                Demo mode — any email and password. Tenant isolation ensured via subdomain/slug mapping.
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="relative z-10 px-8 pb-8 text-xs text-white/60">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <span>© {new Date().getFullYear()} HR Autonomous OS</span>
          <div className="flex items-center gap-4">
            <a className="hover:text-white" href="/privacy-policy">Privacy</a>
            <a className="hover:text-white" href="/terms-of-service">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Protected Route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem("srp_auth_token");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <TenantProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <TenantDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/billing"
              element={
                <ProtectedRoute>
                  <BillingDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/metrics"
              element={
                <ProtectedRoute>
                  <ObservabilityDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/apps"
              element={
                <ProtectedRoute>
                  <AppManagementConsole />
                </ProtectedRoute>
              }
            />
            <Route
              path="/apps/:appId"
              element={
                <ProtectedRoute>
                  <AppDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/orchestrator"
              element={
                <ProtectedRoute>
                  <OrchestratorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute>
                  <RBACManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <PlatformAdminConsole />
                </ProtectedRoute>
              }
            />

            {/* Public informational routes */}
            <Route path="/about" element={<AboutPage />} />
            <Route path="/how-it-works" element={<HowItWorksPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
            <Route path="/terms-of-service" element={<TermsOfServicePage />} />

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/help"
              element={
                <ProtectedRoute>
                  <HelpPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </TenantProvider>
      </AuthProvider>
    </Router>
  );
};

export default App;
