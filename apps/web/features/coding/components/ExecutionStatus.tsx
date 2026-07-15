"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface ExecutionStatusProps {
  status: "idle" | "running" | "submitting" | "completed" | "error";
  passedCount?: number;
  totalCount?: number;
  executionMs?: number;
  className?: string;
}

export const ExecutionStatus = memo(function ExecutionStatus({
  status,
  passedCount = 0,
  totalCount = 0,
  executionMs,
  className,
}: ExecutionStatusProps) {
  if (status === "idle") return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium",
        status === "running" || status === "submitting" ? "bg-info-bg text-info-foreground" :
        status === "completed" && passedCount === totalCount ? "bg-success-bg text-success-foreground" :
        status === "completed" ? "bg-warning-bg text-warning-foreground" :
        "bg-destructive/10 text-destructive",
        className,
      )}
    >
      {status === "running" || status === "submitting" ? (
        <><Loader2 className="h-3.5 w-3.5 animate-spin" /> {status === "running" ? "Running..." : "Submitting..."}</>
      ) : status === "completed" ? (
        <><CheckCircle2 className="h-3.5 w-3.5" /> {passedCount}/{totalCount} tests passed</>
      ) : (
        <><XCircle className="h-3.5 w-3.5" /> Error</>
      )}
      {executionMs != null && (
        <span className="text-muted-foreground"><Clock className="inline h-3 w-3" /> {executionMs}ms</span>
      )}
    </motion.div>
  );
});
