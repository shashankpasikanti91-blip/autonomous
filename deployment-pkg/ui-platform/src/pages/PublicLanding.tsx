import React from 'react';
import { BarChart, TrendingUp, Users, Zap, Shield, Globe } from 'lucide-react';

export default function PublicLandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* Navigation */}
      <nav className="fixed w-full top-0 z-50 bg-black/20 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-pink-400 bg-clip-text text-transparent">
            HR Autonomous OS
          </div>
          <div className="flex gap-8">
            <a href="#features" className="hover:text-indigo-400 transition">Features</a>
            <a href="#benefits" className="hover:text-indigo-400 transition">Benefits</a>
            <a href="#pricing" className="hover:text-indigo-400 transition">Analytics</a>
            <button className="bg-gradient-to-r from-indigo-500 to-pink-500 px-6 py-2 rounded-full hover:shadow-lg hover:shadow-indigo-500/50 transition">
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 text-center">
        <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
          AI-Powered HR Automation Platform
        </h1>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-8">
          Transform your HR operations with intelligent automation, real-time analytics, and AI-driven insights. 
          Say goodbye to manual tasks and hello to data-driven decisions.
        </p>
        <div className="flex gap-4 justify-center mb-12">
          <button className="bg-gradient-to-r from-indigo-500 to-pink-500 px-8 py-4 rounded-lg font-bold text-lg hover:shadow-2xl hover:shadow-indigo-500/30 transition transform hover:scale-105">
            Start Free Trial
          </button>
          <button className="border border-indigo-400 px-8 py-4 rounded-lg font-bold text-lg hover:bg-indigo-400/10 transition">
            Watch Demo
          </button>
        </div>
        <div className="grid grid-cols-3 gap-8 max-w-3xl mx-auto mt-16">
          <div className="text-center">
            <div className="text-4xl font-bold text-indigo-400">95%</div>
            <p className="text-gray-400">Time Saved</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-pink-400">500+</div>
            <p className="text-gray-400">Organizations</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-cyan-400">4.8★</div>
            <p className="text-gray-400">User Rating</p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">Powerful Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: <BarChart className="w-8 h-8" />,
                title: "Advanced Analytics",
                desc: "Real-time dashboards with PowerBI integration for deep insights"
              },
              {
                icon: <Zap className="w-8 h-8" />,
                title: "AI Automation",
                desc: "Intelligent workflows that learn and adapt to your processes"
              },
              {
                icon: <Users className="w-8 h-8" />,
                title: "Multi-Tenant",
                desc: "Manage multiple clients and departments in one platform"
              },
              {
                icon: <Shield className="w-8 h-8" />,
                title: "Enterprise Security",
                desc: "Bank-level encryption and compliance with all standards"
              },
              {
                icon: <Globe className="w-8 h-8" />,
                title: "Global Integration",
                desc: "Connect with 500+ apps and custom integrations"
              },
              {
                icon: <TrendingUp className="w-8 h-8" />,
                title: "Predictive AI",
                desc: "ML-powered forecasting and trend analysis"
              }
            ].map((feature, i) => (
              <div key={i} className="group p-8 rounded-xl bg-white/5 border border-white/10 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition duration-300">
                <div className="text-indigo-400 mb-4 group-hover:scale-110 transition">{feature.icon}</div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-20 px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-4xl font-bold mb-6">Why Choose HR Autonomous OS?</h2>
            <ul className="space-y-4">
              {[
                "✓ 95% reduction in manual HR tasks",
                "✓ Real-time employee insights and analytics",
                "✓ Automated compliance and reporting",
                "✓ Customizable workflows for any industry",
                "✓ Enterprise-grade security and privacy",
                "✓ 24/7 AI-powered support",
                "✓ Seamless integration with existing tools",
                "✓ Scalable from startup to enterprise"
              ].map((benefit, i) => (
                <li key={i} className="text-lg text-gray-300">{benefit}</li>
              ))}
            </ul>
          </div>
          <div className="grid gap-4">
            <div className="bg-gradient-to-br from-indigo-500/20 to-pink-500/20 p-8 rounded-xl border border-indigo-500/30">
              <h3 className="font-bold text-lg mb-2">Revenue Impact</h3>
              <p className="text-2xl font-bold text-indigo-400">+40% Productivity</p>
            </div>
            <div className="bg-gradient-to-br from-cyan-500/20 to-blue-500/20 p-8 rounded-xl border border-cyan-500/30">
              <h3 className="font-bold text-lg mb-2">Cost Savings</h3>
              <p className="text-2xl font-bold text-cyan-400">-60% Manual Work</p>
            </div>
            <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 p-8 rounded-xl border border-green-500/30">
              <h3 className="font-bold text-lg mb-2">ROI Timeline</h3>
              <p className="text-2xl font-bold text-green-400">6 Months</p>
            </div>
          </div>
        </div>
      </section>

      {/* Industries Section */}
      <section className="py-20 px-6 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">Built for Every Industry</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {['Healthcare', 'Finance', 'Retail', 'Technology', 'Education', 'Manufacturing', 'Hospitality', 'Services'].map((industry, i) => (
              <div key={i} className="p-6 rounded-lg bg-white/5 border border-white/10 text-center hover:border-indigo-500/50 transition">
                <h3 className="font-bold">{industry}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-20 px-6 text-center">
        <h2 className="text-4xl font-bold mb-6">Ready to Transform Your HR?</h2>
        <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
          Join 500+ organizations using HR Autonomous OS to automate their operations
        </p>
        <button className="bg-gradient-to-r from-indigo-500 to-pink-500 px-12 py-4 rounded-full font-bold text-lg hover:shadow-2xl hover:shadow-indigo-500/30 transition transform hover:scale-105">
          Start Your Free Trial Today
        </button>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/40 py-12 px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-bold mb-4">Product</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition">Features</a></li>
              <li><a href="#" className="hover:text-white transition">Pricing</a></li>
              <li><a href="#" className="hover:text-white transition">Enterprise</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-4">Company</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition">About</a></li>
              <li><a href="#" className="hover:text-white transition">Blog</a></li>
              <li><a href="#" className="hover:text-white transition">Careers</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-4">Support</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition">Help Center</a></li>
              <li><a href="#" className="hover:text-white transition">Documentation</a></li>
              <li><a href="#" className="hover:text-white transition">API Docs</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-4">Legal</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition">Privacy</a></li>
              <li><a href="#" className="hover:text-white transition">Terms</a></li>
              <li><a href="#" className="hover:text-white transition">Security</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-white/10 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2026 HR Autonomous OS. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
