"use client";

import { motion } from "framer-motion";
import { SectionTitle } from "@/components/marketing/section-title";

export function Reports() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="Evaluation Reports"
          title="Deep insights from every interview"
          description="Each session generates a comprehensive report with dimension scores, question-level feedback, and actionable improvement areas."
        />

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mt-16 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-card to-background shadow-2xl"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/screenshots/insights.png"
            alt="Tayari AI evaluation reports screen"
            className="block h-auto w-full object-cover"
          />
        </motion.div>
      </div>
    </section>
  );
}
