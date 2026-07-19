"use client";

import { memo, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Brain, Code2, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TranscriptEntry, Question } from "@/features/interview/lib/session-types";
import type { RunCodeResult, SubmissionResult } from "@/features/coding/api/coding";

interface ChatEntry {
  type: "question" | "answer" | "code_submit" | "test_result" | "hint" | "thinking";
  text: string;
  timestamp: number;
  metadata?: {
    passed?: number;
    total?: number;
    language?: string;
  };
}

interface CodingChatPanelProps {
  entries: ChatEntry[];
  isAiThinking: boolean;
  className?: string;
}

export const CodingChatPanel = memo(function CodingChatPanel({
  entries,
  isAiThinking,
  className,
}: CodingChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length, isAiThinking]);

  return (
    <div className={cn("flex h-full flex-col overflow-hidden border-r border-border bg-card", className)}>
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Brain className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold">Interview Chat</h3>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {entries.map((entry, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
              "rounded-lg px-3 py-2 text-sm",
              entry.type === "question" && "bg-muted/60",
              entry.type === "answer" && "bg-primary/5 ml-4",
              entry.type === "code_submit" && "bg-info-bg/30 ml-4 border border-info-border/30",
              entry.type === "test_result" && "bg-card border border-border",
              entry.type === "hint" && "bg-warning-bg/30 border border-warning-border/30",
            )}
          >
            <div className="mb-0.5 flex items-center gap-1.5">
              {entry.type === "question" && <Brain className="h-3 w-3 text-primary" />}
              {entry.type === "answer" && <Code2 className="h-3 w-3 text-muted-foreground" />}
              {entry.type === "code_submit" && <Code2 className="h-3 w-3 text-info" />}
              {entry.type === "test_result" && (
                (entry.metadata?.passed ?? 0) === (entry.metadata?.total ?? 0)
                  ? <CheckCircle2 className="h-3 w-3 text-success" />
                  : <XCircle className="h-3 w-3 text-destructive" />
              )}
              <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                {entry.type === "question" && "Interviewer"}
                {entry.type === "answer" && "You"}
                {entry.type === "code_submit" && "Submitted"}
                {entry.type === "test_result" && `Tests: ${entry.metadata?.passed ?? 0}/${entry.metadata?.total ?? 0}`}
                {entry.type === "hint" && "Hint"}
              </span>
            </div>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{entry.text}</p>
          </motion.div>
        ))}

        {isAiThinking && (
          <div className="flex items-center gap-2 rounded-lg bg-info-bg/30 px-3 py-2 text-sm text-info-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            AI is thinking...
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
});
