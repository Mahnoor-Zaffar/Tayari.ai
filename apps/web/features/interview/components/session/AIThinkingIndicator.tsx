"use client";

import { memo, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface AIThinkingIndicatorProps {
  isThinking: boolean;
}

const THINKING_MESSAGES = [
  "Thinking",
  "Considering your response",
  "Formulating next question",
  "Analyzing your answer",
];

export const AIThinkingIndicator = memo(function AIThinkingIndicator({
  isThinking,
}: AIThinkingIndicatorProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const [dots, setDots] = useState("");

  useEffect(() => {
    if (!isThinking) {
      setMessageIndex(0);
      setDots("");
      return;
    }
    const msgInterval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % THINKING_MESSAGES.length);
    }, 3000);
    const dotInterval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 500);
    return () => {
      clearInterval(msgInterval);
      clearInterval(dotInterval);
    };
  }, [isThinking]);

  return (
    <AnimatePresence>
      {isThinking && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="flex items-center gap-3 rounded-lg border border-info-border bg-info-bg/50 p-4"
          role="status"
          aria-live="polite"
          aria-label="AI is thinking"
        >
          <div className="flex gap-1">
            <motion.span
              className="h-2 w-2 rounded-full bg-info"
              animate={{ y: [0, -6, 0] }}
              transition={{ repeat: Infinity, duration: 0.6, ease: "easeInOut", delay: 0 }}
            />
            <motion.span
              className="h-2 w-2 rounded-full bg-info"
              animate={{ y: [0, -6, 0] }}
              transition={{ repeat: Infinity, duration: 0.6, ease: "easeInOut", delay: 0.15 }}
            />
            <motion.span
              className="h-2 w-2 rounded-full bg-info"
              animate={{ y: [0, -6, 0] }}
              transition={{ repeat: Infinity, duration: 0.6, ease: "easeInOut", delay: 0.3 }}
            />
          </div>
          <p className="text-sm text-info-foreground">
            {THINKING_MESSAGES[messageIndex]}
            {dots}
          </p>
        </motion.div>
      )}
    </AnimatePresence>
  );
});
