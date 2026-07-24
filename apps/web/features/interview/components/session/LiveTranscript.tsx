"use client";

import { memo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { TranscriptEntry } from "@/features/interview/lib/session-types";

interface LiveTranscriptProps {
  transcript: TranscriptEntry[];
}

const SCROLL_NEAR_BOTTOM_PX = 120;

export const LiveTranscript = memo(function LiveTranscript({ transcript }: LiveTranscriptProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const isNearBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < SCROLL_NEAR_BOTTOM_PX;
    if (isNearBottom) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        rafRef.current = null;
      });
    }
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [transcript.length, transcript[transcript.length - 1]?.text]);

  if (transcript.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">The transcript will appear here.</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="space-y-3 overflow-y-auto"
      role="log"
      aria-label="Live transcript"
      aria-live="polite"
    >
      <AnimatePresence initial={false}>
        {transcript.map((entry, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
              "rounded-lg px-3 py-2",
              entry.speaker === "ai" ? "bg-muted/50" : "bg-primary/5 ml-8",
            )}
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              {entry.speaker === "ai" ? "Interviewer" : "You"}
            </p>
            <p className="mt-0.5 text-sm leading-relaxed">{entry.text}</p>
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
});
