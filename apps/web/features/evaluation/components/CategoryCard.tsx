"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface CategoryCardProps {
  label: string;
  score: number;
  evidence?: string;
  index: number;
  className?: string;
}

export const CategoryCard = memo(function CategoryCard({
  label, score, evidence, index, className,
}: CategoryCardProps) {
  const pct = (score / 5) * 100;
  const color = score >= 4 ? "bg-success" : score >= 3 ? "bg-warning" : "bg-destructive";

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
      className={cn("space-y-1.5 rounded-lg border border-border bg-card p-3", className)}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className={cn("text-sm font-bold tabular-nums", score >= 4 ? "text-success" : score >= 3 ? "text-warning" : "text-destructive")}>
          {score.toFixed(1)}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className={cn("h-full rounded-full", color)}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, delay: index * 0.08 + 0.2, ease: "easeOut" }}
        />
      </div>
      {evidence && <p className="text-xs text-muted-foreground italic">&ldquo;{evidence}&rdquo;</p>}
    </motion.div>
  );
});
