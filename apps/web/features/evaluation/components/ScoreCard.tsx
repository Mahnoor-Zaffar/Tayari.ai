"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ScoreCardProps {
  score: number;
  score100: number;
  label: string;
  verdict?: string;
  size?: "sm" | "lg";
  className?: string;
}

function verdictColor(verdict?: string): string {
  switch (verdict) {
    case "hire": return "text-success";
    case "lean_hire": return "text-warning";
    case "lean_no_hire": return "text-orange-500";
    case "no_hire": return "text-destructive";
    default: return "text-muted-foreground";
  }
}

function verdictLabel(verdict?: string): string {
  switch (verdict) {
    case "hire": return "Hire";
    case "lean_hire": return "Lean Hire";
    case "lean_no_hire": return "Lean No-Hire";
    case "no_hire": return "No Hire";
    case "error": return "Error";
    default: return "Pending";
  }
}

export const ScoreCard = memo(function ScoreCard({
  score,
  score100,
  label,
  verdict,
  size = "lg",
  className,
}: ScoreCardProps) {
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 5) * circumference;

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <div className="relative flex items-center justify-center">
        <svg width={size === "lg" ? 140 : 100} height={size === "lg" ? 140 : 100} className="-rotate-90">
          <circle cx="50%" cy="50%" r="54" fill="none" stroke="hsl(var(--muted))" strokeWidth="8"
            transform={`scale(${size === "lg" ? 1.3 : 0.93})`} style={{ transformOrigin: "center" }} />
          <motion.circle
            cx="50%" cy="50%" r="54" fill="none" stroke="hsl(var(--primary))" strokeWidth="8"
            strokeLinecap="round"
            initial={{ strokeDasharray: circumference, strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: "easeOut" }}
            transform={`scale(${size === "lg" ? 1.3 : 0.93})`}
            style={{ transformOrigin: "center" }}
          />
        </svg>
        <motion.span
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className={cn("absolute text-2xl font-bold tabular-nums", size === "sm" && "text-lg")}
        >
          {score.toFixed(1)}
        </motion.span>
      </div>
      <span className="text-xs text-muted-foreground">{label}</span>
      {verdict && (
        <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-semibold", verdictColor(verdict), "bg-current/10")}>
          {verdictLabel(verdict)}
        </span>
      )}
      <span className="text-[10px] text-muted-foreground">{score100.toFixed(0)}/100</span>
    </div>
  );
});
