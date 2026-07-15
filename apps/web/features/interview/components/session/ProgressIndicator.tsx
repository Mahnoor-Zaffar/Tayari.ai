"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ProgressIndicatorProps {
  current: number;
  total: number;
}

export const ProgressIndicator = memo(function ProgressIndicator({
  current,
  total,
}: ProgressIndicatorProps) {
  const estimatedTotal = Math.max(total, current + 5);
  const pct = estimatedTotal > 0 ? Math.min((current / estimatedTotal) * 100, 100) : 0;

  return (
    <div className="space-y-1" role="progressbar" aria-valuenow={current} aria-valuemin={0} aria-valuemax={estimatedTotal} aria-label="Interview progress">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Progress</span>
        <span>
          {current} question{current !== 1 ? "s" : ""}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
});
