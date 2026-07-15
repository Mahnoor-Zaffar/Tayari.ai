"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ProblemPanelProps {
  title?: string;
  description?: string;
  difficulty?: string;
  examples?: Array<{ input: string; output: string; explanation?: string }>;
  className?: string;
}

export const ProblemPanel = memo(function ProblemPanel({
  title = "Coding Challenge",
  description = "Write a function to solve the problem below.",
  difficulty = "medium",
  examples = [
    { input: "5\n3", output: "8", explanation: "5 + 3 = 8" },
    { input: "10\n20", output: "30" },
  ],
  className,
}: ProblemPanelProps) {
  const diffColor = difficulty === "easy" ? "text-success" : difficulty === "hard" ? "text-destructive" : "text-warning";

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={cn("space-y-4 overflow-y-auto p-4", className)}>
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold">{title}</h2>
        <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium uppercase", diffColor, "bg-current/10")}>
          {difficulty}
        </span>
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>

      {examples.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Examples</h3>
          {examples.map((ex, i) => (
            <div key={i} className="rounded-lg border border-border bg-card p-3 text-sm">
              <div className="mb-1">
                <span className="text-[11px] font-medium uppercase text-muted-foreground">Input:</span>
                <pre className="mt-0.5 rounded bg-muted p-2 font-mono text-xs">{ex.input}</pre>
              </div>
              <div className="mb-1">
                <span className="text-[11px] font-medium uppercase text-muted-foreground">Output:</span>
                <pre className="mt-0.5 rounded bg-muted p-2 font-mono text-xs">{ex.output}</pre>
              </div>
              {ex.explanation && (
                <p className="mt-1 text-xs text-muted-foreground">{ex.explanation}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
});
