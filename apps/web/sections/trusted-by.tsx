"use client";

import { motion } from "framer-motion";

const companies = [
  "Google",
  "Meta",
  "Amazon",
  "Microsoft",
  "Apple",
  "Netflix",
  "Stripe",
  "Spotify",
  "Adobe",
  "Nvidia",
];

export function TrustedBy() {
  return (
    <section className="border-y border-white/5 py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="mb-8 text-center text-xs font-medium uppercase tracking-widest text-muted-foreground">
          Interview prep trusted by candidates targeting
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6">
          {companies.map((name, i) => (
            <motion.span
              key={name}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="text-sm font-semibold text-muted-foreground/40 transition-colors hover:text-muted-foreground/70"
            >
              {name}
            </motion.span>
          ))}
        </div>
      </div>
    </section>
  );
}
