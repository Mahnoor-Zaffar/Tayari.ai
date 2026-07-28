"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { GradientButton } from "@/components/marketing/gradient-button";

export function CTA() {
  return (
    <section className="relative border-t border-white/5 py-24 sm:py-32">
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none" />
      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="space-y-6"
        >
          <h2 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Ready to ace your interview?
          </h2>
          <p className="mx-auto max-w-xl text-lg leading-relaxed text-muted-foreground">
            Join thousands of engineers who use Tayari to prepare for technical interviews at the
            world&apos;s top companies.
          </p>
          <div className="flex items-center justify-center gap-4 pt-4">
            <GradientButton href="/auth/register" size="lg">
              Start Your First Interview <ArrowRight className="ml-2 h-4 w-4" />
            </GradientButton>
            <GradientButton href="#features" variant="outline" size="lg">
              Explore Features
            </GradientButton>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
