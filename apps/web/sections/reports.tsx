"use client";

import { motion } from "framer-motion";
import { SectionTitle } from "@/components/marketing/section-title";

const DIMENSIONS = [
  { label: "Problem Solving", score: 88, color: "from-blue-500 to-cyan-400" },
  { label: "Communication", score: 82, color: "from-purple-500 to-pink-400" },
  { label: "Code Quality", score: 75, color: "from-emerald-500 to-green-400" },
  { label: "Technical Depth", score: 90, color: "from-amber-500 to-orange-400" },
];

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
          <div className="grid grid-cols-1 gap-px bg-white/5 lg:grid-cols-5">
            <div className="col-span-3 space-y-6 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Overall Score</p>
                  <p className="text-4xl font-bold text-primary">4.2</p>
                  <p className="text-sm text-muted-foreground">out of 5.0</p>
                </div>
                <div className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-center">
                  <p className="text-xs text-muted-foreground">Verdict</p>
                  <p className="text-lg font-bold text-primary">Strong Hire</p>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium">Dimension Scores</p>
                {DIMENSIONS.map((d) => (
                  <div key={d.label} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span>{d.label}</span>
                      <span className="font-medium">{d.score}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${d.score}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 1, delay: 0.3 }}
                        className={`h-full rounded-full bg-gradient-to-r ${d.color}`}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium">Key Strengths</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    "Clear problem decomposition",
                    "Efficient O(n) solution",
                    "Good test coverage",
                    "Strong communication",
                  ].map((s) => (
                    <span
                      key={s}
                      className="rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1 text-xs text-emerald-400"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium">Areas to Improve</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    "Edge case handling",
                    "Space complexity analysis",
                    "Alternative approaches",
                  ].map((s) => (
                    <span
                      key={s}
                      className="rounded-full border border-amber-500/20 bg-amber-500/5 px-3 py-1 text-xs text-amber-400"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="col-span-2 border-t border-white/5 p-6 lg:border-t-0 lg:border-l">
              <p className="mb-4 text-sm font-medium">Question Breakdown</p>
              <div className="space-y-3">
                {[
                  { q: "Longest consecutive sequence", s: 4.5 },
                  { q: "Design a rate limiter", s: 4.0 },
                  { q: "Merge k sorted lists", s: 3.5 },
                  { q: "System design: URL shortener", s: 4.8 },
                ].map((item) => (
                  <div key={item.q} className="rounded-lg border border-white/5 bg-card/50 p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{item.q}</span>
                      <span className="text-sm font-bold text-primary">{item.s}</span>
                    </div>
                    <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary/40"
                        style={{ width: `${(item.s / 5) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-xl border border-white/5 bg-card/50 p-4">
                <p className="mb-2 text-sm font-medium">Recommendations</p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-primary" />
                    Practice more space-time complexity analysis
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-primary" />
                    Focus on edge cases in your next session
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-primary" />
                    Review alternative approaches to classic problems
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
