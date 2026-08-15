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
    image: (
      <div className="grid grid-cols-2 gap-3 p-6">
        <div className="col-span-2 rounded-xl border border-white/5 bg-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Total Interviews</p>
              <p className="text-2xl font-bold">24</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Avg Score</p>
              <p className="text-2xl font-bold text-primary">84%</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-white/5 bg-card p-4">
          <p className="text-xs text-muted-foreground">Streak</p>
          <p className="text-xl font-bold">5 days</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-card p-4">
          <p className="text-xs text-muted-foreground">Completed</p>
          <p className="text-xl font-bold">18</p>
        </div>
      </div>
    ),
  },
  {
    title: "Interview Setup Wizard",
    description:
      "Configure every aspect of your interview — type, company, role, difficulty, and duration. Upload your resume for context-aware questions.",
    icon: Settings,
    image: (
      <div className="space-y-3 p-6">
        <div className="flex gap-2">
          {["Coding", "System Design", "Behavioral"].map((t) => (
            <div
              key={t}
              className="rounded-lg border border-white/5 bg-card px-4 py-2 text-sm font-medium text-primary"
            >
              {t}
            </div>
          ))}
        </div>
        <div className="rounded-xl border border-white/5 bg-card p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-medium">Target Company</span>
            <span className="text-sm text-muted-foreground">Google</span>
          </div>
          <div className="h-2 rounded-full bg-muted">
            <div className="h-2 w-3/4 rounded-full bg-primary/40" />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">Setup progress: 75%</p>
        </div>
      </div>
    ),
  },
  {
    title: "Detailed Evaluation Reports",
    description:
      "Every interview generates a multi-dimension report with scores, a hire verdict, and specific strengths and areas for improvement.",
    icon: FileText,
    image: (
      <div className="space-y-3 p-6">
        <div className="flex items-center justify-between rounded-xl border border-white/5 bg-card p-4">
          <span className="text-sm font-medium">Overall Score</span>
          <span className="text-2xl font-bold text-primary">4.2/5</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: "Problem Solving", score: 4.5 },
            { label: "Communication", score: 4.0 },
            { label: "Code Quality", score: 3.8 },
            { label: "Technical Depth", score: 4.2 },
          ].map((d) => (
            <div key={d.label} className="rounded-lg border border-white/5 bg-card p-3">
              <p className="text-xs text-muted-foreground">{d.label}</p>
              <p className="text-lg font-semibold">{d.score}</p>
            </div>
          ))}
        </div>
        <div className="rounded-lg border border-primary/10 bg-primary/5 p-3">
          <p className="text-xs font-medium text-primary">Hire Verdict</p>
          <p className="text-sm">Strong Hire — Excellent performance across all dimensions</p>
        </div>
      </div>
    ),
  },
  {
    title: "Performance Analytics",
    description:
      "Track your improvement over time with daily, weekly, and monthly charts. Spot trends and focus on weak areas.",
    icon: TrendingUp,
    image: (
      <div className="p-6">
        <div className="rounded-xl border border-white/5 bg-card p-4">
          <p className="mb-4 text-sm font-medium">Interview Activity</p>
          <div className="flex items-end gap-2" style={{ height: 100 }}>
            {[40, 65, 45, 80, 55, 90, 70, 85, 60, 95, 75, 88].map((h, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-gradient-to-t from-primary/60 to-primary/30"
                  style={{ height: `${h}%` }}
                />
                <span className="text-[10px] text-muted-foreground">W{i + 1}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    ),
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
                  {item.image}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
