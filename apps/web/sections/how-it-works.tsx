"use client";

import { Settings, MessageCircle, Code, BarChart3 } from "lucide-react";
import { motion } from "framer-motion";
import { SectionTitle } from "@/components/marketing/section-title";

const STEPS = [
  {
    icon: Settings,
    title: "Configure Your Interview",
    description:
      "Choose your target company, role, experience level, and interview type. Upload your resume for tailored questions.",
  },
  {
    icon: MessageCircle,
    title: "Talk to the AI",
    description:
      "Start a live conversation with the AI interviewer. Speak naturally or type — the AI adapts to your communication style.",
  },
  {
    icon: Code,
    title: "Solve Problems",
    description:
      "Tackle coding challenges in the built-in editor or discuss system design trade-offs. The AI probes your reasoning in real time.",
  },
  {
    icon: BarChart3,
    title: "Receive Detailed Report",
    description:
      "Get scored across multiple dimensions with a hire verdict, strengths, improvements, and question-level breakdowns.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="How It Works"
          title="From setup to score in minutes"
          description="No scheduling, no waiting. Start an interview whenever you're ready."
        />

        <div className="relative mt-20">
          <div className="absolute left-1/2 top-0 hidden h-full w-px -translate-x-1/2 bg-gradient-to-b from-primary/40 via-primary/20 to-transparent lg:block" />

          <div className="space-y-16 lg:space-y-24">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className={`relative flex flex-col items-center gap-8 lg:flex-row ${
                  i % 2 === 1 ? "lg:flex-row-reverse" : ""
                }`}
              >
                <div className="flex-1">
                  <div className={`space-y-4 ${i % 2 === 1 ? "lg:text-right" : ""}`}>
                    <div
                      className={`flex items-center gap-4 ${i % 2 === 1 ? "lg:flex-row-reverse" : ""}`}
                    >
                      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-purple-600/10 ring-1 ring-primary/20">
                        <step.icon className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <span className="text-sm font-medium text-primary">Step {i + 1}</span>
                        <h3 className="text-xl font-semibold">{step.title}</h3>
                      </div>
                    </div>
                    <p className="text-muted-foreground leading-relaxed">{step.description}</p>
                  </div>
                </div>

                <div className="relative flex h-12 w-12 items-center justify-center rounded-full border border-white/10 bg-card lg:absolute lg:left-1/2 lg:-translate-x-1/2">
                  <div className="h-3 w-3 rounded-full bg-primary" />
                </div>

                <div className="flex-1" />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
