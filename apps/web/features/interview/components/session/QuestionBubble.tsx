"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Volume2, Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Question } from "@/features/interview/lib/session-types";

interface QuestionBubbleProps {
  question: Question;
  isCurrent: boolean;
}

export const QuestionBubble = memo(function QuestionBubble({
  question,
  isCurrent,
}: QuestionBubbleProps) {
  const isFirst = question.type === "initial";

  return (
    <motion.div
      initial={isCurrent ? { opacity: 0, y: 20 } : undefined}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn(
        "rounded-xl border p-4",
        isCurrent && "border-primary/30 bg-primary/5 shadow-sm",
        !isCurrent && "border-border bg-card",
      )}
    >
      <div className="mb-2 flex items-center gap-2">
        <div
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-full",
            isFirst ? "bg-primary" : "bg-muted",
          )}
        >
          {isFirst ? (
            <Volume2 className="h-3 w-3 text-primary-foreground" />
          ) : (
            <Lightbulb className="h-3 w-3 text-muted-foreground" />
          )}
        </div>
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          {isFirst ? "Interviewer" : "Follow-up"}
        </span>
        {isCurrent && (
          <span className="ml-auto rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
            Current
          </span>
        )}
      </div>
      <p className="text-sm leading-relaxed">{question.text}</p>
    </motion.div>
  );
});
