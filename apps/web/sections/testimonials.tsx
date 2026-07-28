"use client";

import { motion } from "framer-motion";
import { SectionTitle } from "@/components/marketing/section-title";

const TESTIMONIALS = [
  {
    name: "Sarah Chen",
    role: "Software Engineer at Stripe",
    content:
      "Tayari's AI interviews felt remarkably close to the real thing. The system design session prepared me for questions I actually got in my Stripe interview.",
  },
  {
    name: "James Okonkwo",
    role: "Senior Frontend Engineer at Vercel",
    content:
      "I used Tayari for two weeks before my interviews. The detailed feedback on code quality and communication helped me identify blind spots I didn't know I had.",
  },
  {
    name: "Priya Patel",
    role: "Engineering Manager at Microsoft",
    content:
      "The behavioral interview module is excellent. The AI probes your answers with follow-ups that feel natural, not scripted. It's like practicing with a real interviewer.",
  },
];

export function Testimonials() {
  return (
    <section className="relative border-y border-white/5 py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="Testimonials"
          title="What our users say"
          description="Hear from engineers who used Tayari to prepare for their interviews."
        />

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="rounded-2xl border border-white/5 bg-card p-6"
            >
              <svg className="mb-4 h-6 w-6 text-primary/40" fill="currentColor" viewBox="0 0 24 24">
                <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10H14.017zM0 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151C7.546 6.068 5.983 8.789 5.983 11H10v10H0z" />
              </svg>
              <p className="text-sm leading-relaxed text-muted-foreground">{t.content}</p>
              <div className="mt-6 border-t border-white/5 pt-4">
                <p className="text-sm font-medium">{t.name}</p>
                <p className="text-xs text-muted-foreground">{t.role}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
