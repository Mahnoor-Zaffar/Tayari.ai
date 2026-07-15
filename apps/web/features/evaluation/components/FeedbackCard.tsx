"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Lightbulb, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface FeedbackCardProps {
  strengths: string[];
  improvements: string[];
  className?: string;
}

export const FeedbackCard = memo(function FeedbackCard({
  strengths, improvements, className,
}: FeedbackCardProps) {
  return (
    <div className={cn("grid gap-4 sm:grid-cols-2", className)}>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }} className="rounded-lg border border-border bg-card p-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-success">
          <TrendingUp className="h-4 w-4" /> Strengths
        </h3>
        <ul className="mt-3 space-y-2">
          {strengths.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
              <span>{s}</span>
            </li>
          ))}
          {strengths.length === 0 && <li className="text-sm text-muted-foreground">No strengths recorded.</li>}
        </ul>
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }} className="rounded-lg border border-border bg-card p-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-warning">
          <Lightbulb className="h-4 w-4" /> To Improve
        </h3>
        <ul className="mt-3 space-y-2">
          {improvements.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
              <span>{s}</span>
            </li>
          ))}
          {improvements.length === 0 && <li className="text-sm text-muted-foreground">No improvements suggested.</li>}
        </ul>
      </motion.div>
    </div>
  );
});
