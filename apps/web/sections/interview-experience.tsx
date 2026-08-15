"use client";

import { motion } from "framer-motion";
import { SectionTitle } from "@/components/marketing/section-title";

export function InterviewExperience() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="Interview Experience"
          title="A premium interview environment"
          description="Every detail is designed to mirror real technical interviews — from the AI interviewer to the coding environment."
        />
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mt-16 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-card to-background shadow-2xl"
        >
          <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="flex gap-1.5">
                <div className="h-3 w-3 rounded-full bg-red-500/60" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
                <div className="h-3 w-3 rounded-full bg-green-500/60" />
              </div>
              <span className="text-sm font-medium">Coding Interview — Senior Engineer</span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                Connected
              </span>
              <span className="font-mono text-primary">22:34</span>
            </div>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/screenshots/coding-interview.png"
            alt="Tayari AI coding interview screen"
            className="block h-auto w-full object-cover"
          />
        </motion.div>
      </div>
    </section>
  );
}
