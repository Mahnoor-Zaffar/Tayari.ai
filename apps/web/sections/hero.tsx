"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { GradientButton } from "@/components/marketing/gradient-button";

export function Hero() {
  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 pt-24">
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-background pointer-events-none" />
      <div className="absolute left-1/2 top-1/3 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-primary/10 blur-[120px] pointer-events-none" />

      <div className="relative z-10 mx-auto max-w-4xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-block rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-medium text-primary">
            AI-Powered Interview Preparation
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mt-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl"
        >
          Ace Your Next
          <br />
          <span className="bg-gradient-to-r from-primary via-purple-400 to-cyan-400 bg-clip-text text-transparent">
            Technical Interview
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground"
        >
          Practice with lifelike AI interviews that adapt to your responses. Get scored evaluations,
          track your progress, and walk into your next interview with confidence.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-8 flex items-center justify-center gap-4"
        >
          <GradientButton href="/auth/register" size="lg">
            Start Interview <ArrowRight className="ml-2 h-4 w-4" />
          </GradientButton>
          <GradientButton href="#how-it-works" variant="outline" size="lg">
            <Play className="mr-2 h-4 w-4" /> View Demo
          </GradientButton>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.5 }}
        className="relative z-10 mt-16 w-full max-w-6xl"
      >
        <div className="relative mx-4 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-card to-background shadow-2xl">
          <div className="flex items-center gap-2 border-b border-white/5 px-4 py-3">
            <div className="flex gap-1.5">
              <div className="h-3 w-3 rounded-full bg-red-500/60" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
              <div className="h-3 w-3 rounded-full bg-green-500/60" />
            </div>
            <span className="ml-4 text-xs text-muted-foreground">
              tayari.ai — Interview Preparation
            </span>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/screenshots/landing-page.png"
            alt="Tayari AI landing page"
            className="block h-auto w-full object-cover"
          />
        </div>
      </motion.div>
    </section>
  );
}
