"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface TimelineProps {
  questions: Array<{ id: number; text: string; type: string }>;
  className?: string;
}

export const Timeline = memo(function Timeline({ questions, className }: TimelineProps) {
  return (
    <div className={cn("space-y-0", className)}>
      <h3 className="mb-3 text-sm font-semibold">Question Timeline</h3>
      <div className="relative">
        <div className="absolute left-[11px] top-2 h-[calc(100%-16px)] w-0.5 bg-muted" />
        <div className="space-y-4">
          {questions.map((q, i) => (
            <motion.div
              key={q.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-start gap-3"
            >
              <div className={cn(
                "relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
                q.type === "initial" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
              )}>
                {q.type === "initial" ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : (
                  <HelpCircle className="h-3.5 w-3.5" />
                )}
              </div>
              <div className="flex-1 pb-2">
                <p className="text-xs font-medium text-muted-foreground">
                  {q.type === "initial" ? "Opening" : "Follow-up"} #{i + 1}
                </p>
                <p className="mt-0.5 text-sm">{q.text}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
});
