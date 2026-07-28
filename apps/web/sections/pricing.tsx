"use client";

import { SectionTitle } from "@/components/marketing/section-title";
import { PricingCard } from "@/components/marketing/pricing-card";

const PLANS = [
  {
    name: "Free",
    price: "Free",
    description: "Get started with basic practice sessions",
    features: [
      "10 interviews per month",
      "Coding & behavioral formats",
      "Basic evaluation reports",
      "Progress tracking",
    ],
  },
  {
    name: "Pro",
    price: "$19",
    description: "Serious preparation with full access",
    features: [
      "Unlimited interviews",
      "All interview formats",
      "Detailed AI evaluations",
      "Resume & JD analysis",
      "Performance analytics",
      "Priority support",
    ],
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "$49",
    description: "For teams and organizations",
    features: [
      "Everything in Pro",
      "Team dashboard",
      "Custom interview templates",
      "API access",
      "Dedicated support",
      "Custom integrations",
    ],
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="Pricing"
          title="Simple, transparent pricing"
          description="Start free, upgrade when you're ready to go further."
        />
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {PLANS.map((plan, i) => (
            <PricingCard key={plan.name} {...plan} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
