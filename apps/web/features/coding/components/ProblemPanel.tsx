"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ProblemPanelProps {
  title?: string;
  description?: string;
  difficulty?: string;
  examples?: Array<{ input: string; output: string; explanation?: string }>;
  constraints?: string[];
  className?: string;
}

const DEFAULT_PROBLEM = {
  title: "Two Sum",
  description:
    "Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target. You may assume each input has exactly one solution, and you may not use the same element twice. Return the indices in the order they appear in the input, separated by a single space.",
  difficulty: "medium",
  examples: [
    {
      input: "4\n2 7 11 15\n9",
      output: "0 1",
      explanation: "Because nums[0] + nums[1] == 9, we return 0 1.",
    },
    {
      input: "3\n3 2 4\n6",
      output: "1 2",
      explanation: "Because nums[1] + nums[2] == 6, we return 1 2.",
    },
  ],
  constraints: [
    "2 <= nums.length <= 10^4",
    "-10^9 <= nums[i] <= 10^9",
    "-10^9 <= target <= 10^9",
    "Exactly one valid answer exists.",
  ],
};

export const ProblemPanel = memo(function ProblemPanel({
  title = DEFAULT_PROBLEM.title,
  description = DEFAULT_PROBLEM.description,
  difficulty = DEFAULT_PROBLEM.difficulty,
  examples = DEFAULT_PROBLEM.examples,
  constraints = DEFAULT_PROBLEM.constraints,
  className,
}: ProblemPanelProps) {
  const diffColor =
    difficulty === "easy"
      ? "text-success"
      : difficulty === "hard"
        ? "text-destructive"
        : "text-warning";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn("space-y-4 overflow-y-auto p-4", className)}
    >
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold">{title}</h2>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-[11px] font-medium uppercase",
            diffColor,
            "bg-current/10",
          )}
        >
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
                <span className="text-[11px] font-medium uppercase text-muted-foreground">
                  Input:
                </span>
                <pre className="mt-0.5 rounded bg-muted p-2 font-mono text-xs">{ex.input}</pre>
              </div>
              <div className="mb-1">
                <span className="text-[11px] font-medium uppercase text-muted-foreground">
                  Output:
                </span>
                <pre className="mt-0.5 rounded bg-muted p-2 font-mono text-xs">{ex.output}</pre>
              </div>
              {ex.explanation && (
                <p className="mt-1 text-xs text-muted-foreground">{ex.explanation}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {constraints.length > 0 && (
        <div className="space-y-1.5">
          <h3 className="text-sm font-semibold">Constraints</h3>
          <ul className="list-inside list-disc space-y-1 text-xs text-muted-foreground">
            {constraints.map((c, i) => (
              <li key={i} className="font-mono">
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
});
