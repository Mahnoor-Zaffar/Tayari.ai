"use client";

import { memo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { TranscriptEntry } from "@/features/interview/lib/session-types";

interface LiveTranscriptProps {
  transcript: TranscriptEntry[];
}

export const LiveTranscript = memo(function LiveTranscript({
  transcript,
}: LiveTranscriptProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript.length]);

  if (transcript.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">The transcript will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3" role="log" aria-label="Live transcript" aria-live="polite">
      <AnimatePresence initial={false}>
        {transcript.map((entry, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
              "rounded-lg px-3 py-2",
              entry.speaker === "ai"
                ? "bg-muted/50"
                : "bg-primary/5 ml-8",
            )}
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              {entry.speaker === "ai" ? "Interviewer" : "You"}
            </p>
            <p className="mt-0.5 text-sm leading-relaxed">
              {entry.text}
            </p>
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
});
