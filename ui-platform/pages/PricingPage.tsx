/**
 * Pricing Page — modern SaaS style with USD pricing
 */

import React, { useState } from "react";
import { InfoNav } from "../components/InfoNav";
import { Footer } from "../components/Footer";

export const PricingPage: React.FC = () => {
  const [annual, setAnnual] = useState(false);

  const plans = [
    {
      name: "Starter",
      tagline: "Custom internal systems",
      monthlyPrice: 49,
      features: [
        "AI template generation",
        "Core business modules",
        "Single deployment environment",
        "Basic run history and logs",
        "Email support",
      ],
      cta: "Get Started",
      ctaHref: "mailto:hello@srpailabs.com?subject=Starter Plan",
    },
    {
      name: "Business",
      tagline: "Extended modules and customization",
      monthlyPrice: 149,
      features: [
        "Everything in Starter",
        "Payroll, CRM, and Invoicing templates",
        "Extended module configuration",
        "Custom fields and workflows",
        "Multi-industry support (7 industries)",
        "Priority support",
      ],
      cta: "Get Started",
      ctaHref: "mailto:hello@srpailabs.com?subject=Business Plan",
      highlighted: true,
    },
    {
      name: "Enterprise",
      tagline: "Dedicated deployment and integrations",
      monthlyPrice: 399,
      features: [
        "Everything in Business",
        "Dedicated deployment environment",
        "Third-party system integrations",
        "Custom compliance rules",
        "Dedicated onboarding and SLA",
        "Custom subdomain (*.autonomous.srpailabs.com)",
      ],
      cta: "Contact Sales",
      ctaHref: "mailto:hello@srpailabs.com?subject=Enterprise Plan",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <InfoNav />

      <main className="flex-1">
        {/* Hero */}
        <section className="max-w-4xl mx-auto px-5 pt-16 pb-12 text-center">
          <span className="inline-block px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-600 text-[11px] font-medium tracking-wide mb-5">
            Pricing
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight mb-4">
            Simple plans for{" "}
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              every team size
            </span>
          </h1>
          <p className="text-sm text-gray-600 leading-relaxed max-w-xl mx-auto mb-6">
            Designed for internal business operations. All plans include AI-generated
            applications and full data ownership.
          </p>

          {/* Annual toggle */}
          <div className="inline-flex items-center gap-3 bg-gray-100 rounded-full px-4 py-2">
            <span className={`text-xs font-medium ${!annual ? "text-gray-900" : "text-gray-400"}`}>Monthly</span>
            <button
              onClick={() => setAnnual(!annual)}
              className={`relative w-9 h-5 rounded-full transition-colors ${annual ? "bg-blue-600" : "bg-gray-300"}`}
              aria-label="Toggle annual billing"
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${annual ? "translate-x-4" : "translate-x-0"}`}
              />
            </button>
            <span className={`text-xs font-medium ${annual ? "text-gray-900" : "text-gray-400"}`}>
              Annual <span className="text-green-600 font-semibold">−20%</span>
            </span>
          </div>
        </section>

        {/* Plans */}
        <section className="max-w-4xl mx-auto px-5 pb-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {plans.map((plan) => {
              const displayPrice = annual
                ? Math.round(plan.monthlyPrice * 0.8)
                : plan.monthlyPrice;
              return (
              <div
                key={plan.name}
                className={`relative bg-white rounded-xl flex flex-col p-6 shadow-sm ${
                  plan.highlighted
                    ? "border border-blue-500 ring-1 ring-blue-500/20"
                    : "border border-gray-200"
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-3 py-0.5 rounded-full bg-blue-600 text-white text-[10px] font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="mb-4">
                  <h3 className={`text-base font-bold mb-0.5 ${plan.highlighted ? "text-blue-600" : "text-gray-900"}`}>
                    {plan.name}
                  </h3>
                  <p className="text-xs text-gray-500">{plan.tagline}</p>
                </div>

                {/* Price */}
                <div className="mb-5">
                  <div className="flex items-end gap-1">
                    <span className="text-3xl font-extrabold text-gray-900">${displayPrice}</span>
                    <span className="text-xs text-gray-500 mb-1">/mo</span>
                  </div>
                  {annual && (
                    <p className="text-[10px] text-green-600 font-medium mt-0.5">
                      Billed annually — save ${Math.round((plan.monthlyPrice - displayPrice) * 12)}/yr
                    </p>
                  )}
                </div>

                <ul className="space-y-2 flex-1 mb-6">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-xs text-gray-700">
                      <span className="text-green-500 shrink-0 mt-0.5 text-[10px]">✓</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>

                <div className="pt-4 border-t border-gray-200">
                  <a
                    href={plan.ctaHref}
                    className={`block text-center py-2 rounded-lg text-xs font-medium transition-colors ${
                      plan.highlighted
                        ? "bg-blue-600 hover:bg-blue-500 text-white"
                        : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                    }`}
                  >
                    {plan.cta}
                  </a>
                </div>
              </div>
              );
            })}
          </div>
        </section>

        {/* All-plans note */}
        <section className="border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-5 py-8 text-center">
            <p className="text-xs text-gray-600">
              All plans include AI-generated structured applications, database tables, module configuration, and full data ownership in your environment. Prices in USD.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default PricingPage;
