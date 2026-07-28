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
          <div className="grid grid-cols-1 lg:grid-cols-2">
            <div className="border-b border-white/5 p-6 lg:border-b-0 lg:border-r">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary to-purple-600 text-sm font-bold text-white">
                  AI
                </div>
                <div>
                  <p className="text-sm font-medium">AI Interviewer</p>
                  <p className="text-xs text-muted-foreground">Senior Backend Engineer at Google</p>
                </div>
              </div>
              <div className="space-y-4">
                <div className="rounded-xl border border-white/5 bg-card/50 p-4">
                  <p className="text-sm leading-relaxed">
                    Let&apos;s start with a problem. Given an array of integers, find the longest
                    consecutive sequence of elements that can be rearranged into a strictly
                    increasing sequence. Walk me through your approach before you start coding.
                  </p>
                  <p className="mt-2 text-xs text-muted-foreground">Asked 2 minutes ago</p>
                </div>
                <div className="rounded-xl border border-primary/10 bg-primary/5 p-4">
                  <p className="text-sm leading-relaxed">
                    I think we can use a hash set for O(1) lookups and then iterate to find sequence
                    starts...
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1.5 flex-1 rounded-full bg-muted">
                      <div className="h-1.5 w-2/3 rounded-full bg-primary/40" />
                    </div>
                    <span className="text-xs text-muted-foreground">Recording</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-sm font-medium">Solution</span>
                <span className="rounded-md border border-white/5 px-2 py-1 text-xs text-muted-foreground">
                  Python
                </span>
              </div>
              <div className="rounded-xl border border-white/5 bg-[#1a1a2e] p-4 font-mono text-sm leading-relaxed">
                <pre className="text-[#e2e8f0]">
                  <span className="text-[#c084fc]">def</span>{" "}
                  <span className="text-[#60a5fa]">longest_consecutive</span>(nums):
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-[#a78bfa]">if</span>{" "}
                  <span className="text-[#f472b6]">not</span> nums:
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                  <span className="text-[#f472b6]">return</span>{" "}
                  <span className="text-[#94a3b8]">0</span>
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;num_set <span className="text-[#c084fc]">=</span>{" "}
                  <span className="text-[#60a5fa]">set</span>(nums)
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;longest <span className="text-[#c084fc]">=</span>{" "}
                  <span className="text-[#94a3b8]">0</span>
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-[#a78bfa]">for</span> num{" "}
                  <span className="text-[#a78bfa]">in</span> nums:
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                  <span className="text-[#a78bfa]">if</span> num{" "}
                  <span className="text-[#c084fc]">-</span>{" "}
                  <span className="text-[#94a3b8]">1</span>{" "}
                  <span className="text-[#a78bfa]">not in</span> num_set:
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;length{" "}
                  <span className="text-[#c084fc]">=</span>{" "}
                  <span className="text-[#94a3b8]">1</span>
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                  <span className="text-[#a78bfa]">while</span> num{" "}
                  <span className="text-[#c084fc]">+</span> length{" "}
                  <span className="text-[#a78bfa]">in</span> num_set:
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;length{" "}
                  <span className="text-[#c084fc]">+=</span>{" "}
                  <span className="text-[#94a3b8]">1</span>
                  <br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;longest{" "}
                  <span className="text-[#c084fc]">=</span>{" "}
                  <span className="text-[#60a5fa]">max</span>(longest, length)
                </pre>
              </div>
              <div className="mt-3 flex gap-2">
                <div className="flex items-center gap-2 rounded-lg border border-white/5 bg-card px-3 py-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span className="text-xs text-muted-foreground">5/8 tests passing</span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-white/5 bg-card px-3 py-2">
                  <span className="text-xs text-muted-foreground">O(n) time</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
