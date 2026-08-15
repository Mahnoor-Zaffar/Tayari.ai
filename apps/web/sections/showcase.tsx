"use client";

import { motion } from "framer-motion";
import { BarChart3, Settings, FileText, TrendingUp } from "lucide-react";
import { SectionTitle } from "@/components/marketing/section-title";

const SHOWCASE_ITEMS = [
  {
    title: "Smart Dashboard",
    description:
      "Get an overview of your interview activity, performance trends, and quick access to start a new session. Your progress at a glance.",
    icon: BarChart3,
    image: "/screenshots/dashboard.png",
  },
  {
    title: "Interview Setup Wizard",
    description:
      "Configure every aspect of your interview — type, company, role, difficulty, and duration. Upload your resume for context-aware questions.",
    icon: Settings,
    image: "/screenshots/interview-setup.png",
  },
  {
    title: "Detailed Evaluation Reports",
    description:
      "Every interview generates a multi-dimension report with scores, a hire verdict, and specific strengths and areas for improvement.",
    icon: FileText,
    image: "/screenshots/reports.png",
  },
  {
    title: "Performance Analytics",
    description:
      "Track your improvement over time with daily, weekly, and monthly charts. Spot trends and focus on weak areas.",
    icon: TrendingUp,
    image: "/screenshots/analytics.png",
  },
];

export function Showcase() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="Product Showcase"
          title="See the platform in action"
          description="Explore the key screens that make Tayari a complete interview preparation tool."
        />
        <div className="mt-16 space-y-24">
          {SHOWCASE_ITEMS.map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6 }}
              className={`flex flex-col items-center gap-12 lg:flex-row ${
                i % 2 === 1 ? "lg:flex-row-reverse" : ""
              }`}
            >
              <div className="flex-1 space-y-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-purple-600/10 ring-1 ring-primary/20">
                  <item.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-2xl font-bold sm:text-3xl">{item.title}</h3>
                <p className="text-lg leading-relaxed text-muted-foreground">{item.description}</p>
              </div>
              <div className="flex-1">
                <div className="overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-card to-background shadow-2xl">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={item.image}
                    alt={`${item.title} — Tayari AI screenshot`}
                    className="block h-auto w-full object-cover"
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
