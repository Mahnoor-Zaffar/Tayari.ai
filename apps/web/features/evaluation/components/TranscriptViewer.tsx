"use client";

import { memo, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface TranscriptViewerProps {
  transcript: Array<{ speaker: string; text: string; timestamp_ms: number }>;
  className?: string;
}

export const TranscriptViewer = memo(function TranscriptViewer({
  transcript, className,
}: TranscriptViewerProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [transcript.length]);

  return (
    <div className={cn("max-h-80 overflow-y-auto rounded-lg border border-border bg-card p-4", className)}>
      <h3 className="mb-3 text-sm font-semibold">Interview Transcript</h3>
      <div className="space-y-3">
        {transcript.map((entry, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.02 }}
            className={cn(
              "rounded-lg px-3 py-2",
              entry.speaker === "ai" || entry.speaker === "assistant"
                ? "bg-muted/50 ml-0"
                : "bg-primary/5 ml-6",
            )}
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              {entry.speaker === "ai" || entry.speaker === "assistant" ? "Interviewer" : "You"}
            </p>
            <p className="mt-0.5 text-sm leading-relaxed">{entry.text}</p>
          </motion.div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
});
