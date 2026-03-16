/**
 * Main App Component — Emergentic AI
 * Application entry point with routing and providers
 */

import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, Link } from "react-router-dom";
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

// ─── Demo accounts quick-fill data ─────────────────────────────────────────
const DEMO_ACCOUNTS = [
  { label: "👑 Founder",   email: "founder@emergentic.ai", password: "Founder@123", role: "Founder" },
  { label: "🔴 Admin",     email: "admin@demo.com",        password: "Demo@123",    role: "Admin" },
  { label: "🏢 Owner",     email: "owner@demo.com",        password: "Demo@123",    role: "Owner" },
  { label: "👥 HR",        email: "hr@demo.com",           password: "Demo@123",    role: "HR Manager" },
  { label: "💰 Finance",   email: "finance@demo.com",      password: "Demo@123",    role: "Finance" },
  { label: "📊 Sales",     email: "sales@demo.com",        password: "Demo@123",    role: "Sales" },
  { label: "💻 Dev",       email: "dev@demo.com",          password: "Demo@123",    role: "Developer" },
  { label: "🔧 Ops",       email: "ops@demo.com",          password: "Demo@123",    role: "Operations" },
];

// ─── Shared nav for public pages ────────────────────────────────────────────
const PublicNav: React.FC = () => (
  <header className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur border-b border-white/10">
    <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2 group">
        <span className="text-xl">⚡</span>
        <span className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">Emergentic AI</span>
      </Link>
      <nav className="hidden md:flex items-center gap-1 text-xs">
        {[
          { label: "How It Works", to: "/how-it-works" },
          { label: "Pricing",      to: "/pricing" },
          { label: "About",        to: "/about" },
        ].map((l) => (
          <Link key={l.to} to={l.to} className="px-3 py-1.5 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors">
            {l.label}
          </Link>
        ))}
        <Link to="/login" className="ml-3 px-4 py-1.5 rounded-md bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold transition-colors">
          Sign In →
        </Link>
      </nav>
    </div>
  </header>
);

// ─── Landing Page ────────────────────────────────────────────────────────────
const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const capabilities = [
    {
      icon: "🤖",
      title: "Intelligent Workflows",
      body: "AI-orchestrated business processes that adapt in real-time. Automate payroll, CRM, compliance, and more with a single prompt.",
    },
    {
      icon: "🏗️",
      title: "Multi-Tenant Apps",
      body: "Spin up fully isolated environments for every client in under 60 seconds. Per-tenant databases, subdomains, and access control.",
    },
    {
      icon: "📊",
      title: "Real-Time Analytics",
      body: "Live observability dashboards, execution logs, and LLM token metrics across every app and workflow in your platform.",
    },
  ];

  const steps = [
    { n: "01", title: "Describe your need", body: "Type a plain-language requirement — 'Build a payroll system for 50 employees with tax deductions'." },
    { n: "02", title: "AI builds your app",  body: "Emergentic AI scaffolds the full application: DB tables, modules, navigation, and summary cards." },
    { n: "03", title: "Operate from day 0", body: "Your app is immediately live. Add records, run workflows, and integrate third-party services." },
  ];

  const plans = [
    { name: "Starter", price: "Free",    desc: "For individuals & prototypes", features: ["3 AI apps", "Core workflows", "Community support"], cta: "Get Started", href: "/login", highlight: false },
    { name: "Professional", price: "$49", period: "/mo", desc: "For growing teams", features: ["Unlimited apps", "7 industry templates", "Priority support", "Custom workflows"], cta: "Start Free Trial", href: "/login", highlight: true },
    { name: "Enterprise", price: "Custom", desc: "For large organisations", features: ["Dedicated deployment", "Custom integrations", "SLA & onboarding", "Custom domain"], cta: "Contact Sales", href: "mailto:hello@emergentic.ai", highlight: false },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <PublicNav />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-25" style={{ backgroundImage: "radial-gradient(circle at 20% 30%, #06b6d4 0, transparent 35%), radial-gradient(circle at 80% 10%, #6366f1 0, transparent 30%), radial-gradient(circle at 50% 80%, #22c55e 0, transparent 25%)" }} />
        <div className="relative max-w-5xl mx-auto px-6 pt-24 pb-28 text-center">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/10 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-300 mb-6">
            ⚡ AI Operating System for Business
          </span>
          <h1 className="text-4xl sm:text-6xl font-bold leading-tight mb-6">
            The AI Operating System<br />
            <span className="bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">for Your Business</span>
          </h1>
          <p className="text-lg text-white/70 max-w-2xl mx-auto mb-10">
            Describe any business process in plain English. Emergentic AI builds, deploys, and operates the full application stack — payroll, CRM, invoicing, HR, and more.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button onClick={() => navigate("/login")} className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 text-white font-semibold shadow-lg hover:translate-y-[-1px] transition">
              Start Building Free →
            </button>
            <button onClick={() => navigate("/how-it-works")} className="px-8 py-3.5 rounded-xl border border-white/20 text-white/80 hover:bg-white/10 transition">
              See How It Works
            </button>
          </div>

          {/* Stats bar */}
          <div className="grid grid-cols-3 gap-6 max-w-lg mx-auto mt-16">
            {[
              { label: "Deployment time", value: "< 60s" },
              { label: "Industry templates", value: "7+" },
              { label: "Data isolation", value: "Per-tenant" },
            ].map((s) => (
              <div key={s.label} className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-center">
                <p className="text-xl font-bold text-cyan-400">{s.value}</p>
                <p className="text-[11px] text-white/50 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400 mb-3">Platform capabilities</p>
          <h2 className="text-2xl sm:text-3xl font-bold">Everything your business needs</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {capabilities.map((c) => (
            <div key={c.title} className="rounded-2xl border border-white/10 bg-white/5 p-6 hover:bg-white/8 transition">
              <div className="text-3xl mb-4">{c.icon}</div>
              <h3 className="text-base font-semibold mb-2">{c.title}</h3>
              <p className="text-sm text-white/60 leading-relaxed">{c.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-white/10 bg-slate-900/50">
        <div className="max-w-4xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400 mb-3">The process</p>
            <h2 className="text-2xl sm:text-3xl font-bold">From idea to running app in 3 steps</h2>
          </div>
          <div className="space-y-4">
            {steps.map((s) => (
              <div key={s.n} className="flex gap-5 items-start rounded-xl border border-white/10 bg-white/5 p-5">
                <div className="shrink-0 w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 font-mono text-xs font-bold">{s.n}</div>
                <div>
                  <h4 className="text-sm font-semibold mb-1">{s.title}</h4>
                  <p className="text-xs text-white/60 leading-relaxed">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400 mb-3">Pricing</p>
          <h2 className="text-2xl sm:text-3xl font-bold">Simple, transparent pricing</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((p) => (
            <div key={p.name} className={`rounded-2xl border p-6 flex flex-col ${p.highlight ? "border-cyan-500 bg-cyan-500/5 ring-1 ring-cyan-500/20" : "border-white/10 bg-white/5"}`}>
              {p.highlight && <div className="text-[10px] font-semibold text-cyan-400 uppercase tracking-widest mb-3">Most Popular</div>}
              <h3 className={`text-base font-bold mb-1 ${p.highlight ? "text-cyan-400" : "text-white"}`}>{p.name}</h3>
              <p className="text-xs text-white/50 mb-4">{p.desc}</p>
              <div className="flex items-end gap-1 mb-5">
                <span className="text-3xl font-extrabold">{p.price}</span>
                {p.period && <span className="text-xs text-white/50 mb-1">{p.period}</span>}
              </div>
              <ul className="space-y-2 flex-1 mb-6">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-xs text-white/70">
                    <span className="text-cyan-400 shrink-0">✓</span>{f}
                  </li>
                ))}
              </ul>
              <a href={p.href} className={`block text-center py-2.5 rounded-lg text-xs font-semibold transition ${p.highlight ? "bg-cyan-500 hover:bg-cyan-400 text-slate-900" : "border border-white/20 hover:bg-white/10 text-white"}`}>
                {p.cta}
              </a>
            </div>
          ))}
        </div>
      </section>

      {/* Demo accounts */}
      <section className="border-t border-white/10 bg-slate-900/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400 mb-3">Try it now</p>
            <h2 className="text-2xl sm:text-3xl font-bold mb-3">Explore with a demo account</h2>
            <p className="text-sm text-white/60">Click any role to instantly access the platform with pre-loaded data.</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.email}
                onClick={() => navigate("/login", { state: { email: a.email, password: a.password } })}
                className="rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 p-4 text-left transition group"
              >
                <p className="text-sm font-semibold mb-1 group-hover:text-cyan-400 transition-colors">{a.label}</p>
                <p className="text-[11px] text-white/50">{a.role}</p>
                <p className="text-[10px] text-white/30 mt-1 truncate">{a.email}</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-slate-950">
        <div className="max-w-5xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-white/40">
          <div className="flex items-center gap-2">
            <span className="text-base">⚡</span>
            <span>© {new Date().getFullYear()} Emergentic AI. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/privacy-policy" className="hover:text-white transition-colors">Privacy</Link>
            <Link to="/terms-of-service" className="hover:text-white transition-colors">Terms</Link>
            <a href="mailto:hello@emergentic.ai" className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

// ─── Login Page ───────────────────────────────────────────────────────────────
const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { login } = useAuth()

  // Accept pre-filled credentials from navigation state (from landing demo cards)
  React.useEffect(() => {
    const state = (window.history.state as any)?.usr;
    if (state?.email) { setEmail(state.email); setPassword(state.password || ''); }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setError('Please enter your email and password.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch {
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fillAndLogin = (acct: typeof DEMO_ACCOUNTS[0]) => {
    setEmail(acct.email);
    setPassword(acct.password);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white">
      <div className="absolute inset-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 20% 20%, #06b6d4 0, transparent 30%), radial-gradient(circle at 80% 0%, #6366f1 0, transparent 25%), radial-gradient(circle at 30% 80%, #22c55e 0, transparent 25%)" }} />

      <header className="relative z-10 px-8 py-6 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <span className="text-xl">⚡</span>
          <span className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">Emergentic AI</span>
        </Link>
        <div className="flex items-center gap-4 text-xs text-white/70">
          <Link className="hover:text-white" to="/about">About</Link>
          <Link className="hover:text-white" to="/pricing">Pricing</Link>
          <Link className="hover:text-white" to="/how-it-works">How it works</Link>
        </div>
      </header>

      <main className="relative z-10 px-6 sm:px-10 pb-14">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          {/* Left: Hero + Quick Demo */}
          <div className="space-y-6 pt-4">
            <div className="space-y-4">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/10 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">
                ⚡ Emergentic AI Platform
              </span>
              <h1 className="text-3xl sm:text-4xl font-bold leading-tight">
                The AI Operating System<br />for Your Business
              </h1>
              <p className="text-sm text-white/70 max-w-xl">
                Build and run intelligent business apps — payroll, CRM, invoicing, HR — from a single control plane.
              </p>
            </div>

            {/* Quick Demo Access */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <p className="text-xs font-semibold text-white/60 uppercase tracking-widest mb-3">⚡ Quick Demo Access</p>
              <div className="grid grid-cols-4 gap-2">
                {DEMO_ACCOUNTS.map((a) => (
                  <button
                    key={a.email}
                    onClick={() => fillAndLogin(a)}
                    className="px-2 py-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/15 text-xs font-medium text-white/80 hover:text-white transition text-center"
                    title={`${a.role} — ${a.email}`}
                  >
                    {a.label}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-white/40 mt-3">Click a role to fill in credentials, then sign in</p>
            </div>
          </div>

          {/* Right: Auth card */}
          <div className="bg-white text-slate-900 rounded-2xl shadow-2xl border border-white/10 p-8 relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: "linear-gradient(120deg, rgba(6,182,212,0.05), rgba(99,102,241,0.07))" }} />
            <div className="relative space-y-6">
              <div>
                <p className="text-xs font-semibold text-cyan-600 uppercase tracking-[0.2em]">Platform access</p>
                <h2 className="text-2xl font-semibold mt-1">Sign in to your workspace</h2>
                <p className="text-sm text-slate-500">Use a demo account or your own credentials.</p>
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
                    className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 outline-none text-sm"
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
                    className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 outline-none text-sm"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-500 text-white text-sm font-semibold shadow-lg hover:translate-y-[-1px] transition disabled:opacity-60"
                >
                  {loading ? "Signing in…" : "Access Workspace →"}
                </button>
              </form>

              {/* Founder shortcut */}
              <div className="border-t border-slate-100 pt-4">
                <p className="text-[11px] text-slate-400 mb-2">Founder access:</p>
                <button
                  onClick={() => fillAndLogin(DEMO_ACCOUNTS[0])}
                  className="w-full py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs text-slate-600 font-medium transition"
                >
                  👑 founder@emergentic.ai / Founder@123
                </button>
              </div>

              <div className="text-[11px] text-slate-500">
                Demo mode available — pre-loaded with sample data across all roles.
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="relative z-10 px-8 pb-8 text-xs text-white/60">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <span>© {new Date().getFullYear()} Emergentic AI</span>
          <div className="flex items-center gap-4">
            <Link className="hover:text-white" to="/privacy-policy">Privacy</Link>
            <Link className="hover:text-white" to="/terms-of-service">Terms</Link>
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
            {/* Public landing page */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes */}
            <Route path="/dashboard" element={<ProtectedRoute><TenantDashboard /></ProtectedRoute>} />
            <Route path="/billing"   element={<ProtectedRoute><BillingDashboard /></ProtectedRoute>} />
            <Route path="/metrics"   element={<ProtectedRoute><ObservabilityDashboard /></ProtectedRoute>} />
            <Route path="/apps"      element={<ProtectedRoute><AppManagementConsole /></ProtectedRoute>} />
            <Route path="/apps/:appId" element={<ProtectedRoute><AppDetailPage /></ProtectedRoute>} />
            <Route path="/orchestrator" element={<ProtectedRoute><OrchestratorPage /></ProtectedRoute>} />
            <Route path="/users"     element={<ProtectedRoute><RBACManagement /></ProtectedRoute>} />
            <Route path="/admin"     element={<ProtectedRoute><PlatformAdminConsole /></ProtectedRoute>} />
            <Route path="/settings"  element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
            <Route path="/help"      element={<ProtectedRoute><HelpPage /></ProtectedRoute>} />

            {/* Public informational routes */}
            <Route path="/about"           element={<AboutPage />} />
            <Route path="/how-it-works"    element={<HowItWorksPage />} />
            <Route path="/pricing"         element={<PricingPage />} />
            <Route path="/privacy-policy"  element={<PrivacyPolicyPage />} />
            <Route path="/terms-of-service" element={<TermsOfServicePage />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </TenantProvider>
      </AuthProvider>
    </Router>
  );
};

export default App;
