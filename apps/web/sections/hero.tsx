"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { GradientButton } from "@/components/marketing/gradient-button";
import { FloatingCard } from "@/components/marketing/floating-card";

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
        className="relative z-10 mt-16 w-full max-w-5xl"
      >
        <div className="relative mx-4 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-card to-background shadow-2xl">
          <div className="flex items-center gap-2 border-b border-white/5 px-4 py-3">
            <div className="flex gap-1.5">
              <div className="h-3 w-3 rounded-full bg-red-500/60" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
              <div className="h-3 w-3 rounded-full bg-green-500/60" />
            </div>
            <span className="ml-4 text-xs text-muted-foreground">
              Interview Session — Senior Backend Engineer at Google
            </span>
          </div>

          <div className="grid grid-cols-3 gap-px bg-white/5">
            <div className="col-span-2 flex flex-col gap-3 p-6">
              <div className="flex items-center gap-3 rounded-lg bg-primary/5 px-4 py-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                  AI
                </div>
                <p className="text-sm">
                  Can you walk me through how you would design a real-time chat system serving 10
                  million users?
                </p>
              </div>
              <div className="flex items-start gap-3 px-4 py-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-bold text-muted-foreground">
                  Y
                </div>
                <div className="flex-1 space-y-2">
                  <p className="text-sm">
                    I would start with WebSocket for persistent connections, then layer in Redis
                    pub/sub for message routing...
                  </p>
                  <div className="h-1 w-full rounded-full bg-muted">
                    <div className="h-1 w-3/5 rounded-full bg-primary/40" />
                  </div>
                  <span className="text-xs text-muted-foreground">Recording... click to stop</span>
                </div>
              </div>
            </div>
            <div className="border-l border-white/5 p-6">
              <div className="space-y-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Time Remaining</p>
                  <p className="text-2xl font-bold text-primary">24:18</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Question</p>
                  <p className="text-sm">3 of 8</p>
                </div>
                <div className="flex gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <svg
                      className="h-4 w-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                      <line x1="12" y1="19" x2="12" y2="23" />
                    </svg>
                  </div>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                    <svg
                      className="h-4 w-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <FloatingCard
          x={20}
          y={-30}
          rotate={-2}
          delay={0.5}
          className="-left-4 top-1/4 hidden lg:block"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
              <div className="h-3 w-3 rounded-full bg-green-500" />
            </div>
            <div>
              <p className="text-sm font-medium">Session Active</p>
              <p className="text-xs text-muted-foreground">Deepgram STT connected</p>
            </div>
          </div>
        </FloatingCard>

        <FloatingCard
          x={-20}
          y={20}
          rotate={3}
          delay={0.8}
          className="-right-4 top-2/3 hidden lg:block"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <span className="text-sm font-bold text-primary">92</span>
            </div>
            <div>
              <p className="text-sm font-medium">Avg Score</p>
              <p className="text-xs text-muted-foreground">Across 15 interviews</p>
            </div>
          </div>
        </FloatingCard>
      </motion.div>
    </section>
  );
}
