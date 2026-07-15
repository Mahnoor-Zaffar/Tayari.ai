"use client";

import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PauseIcon, Play } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PauseOverlayProps {
  isPaused: boolean;
  onResume: () => void;
}

export const PauseOverlay = memo(function PauseOverlay({
  isPaused,
  onResume,
}: PauseOverlayProps) {
  return (
    <AnimatePresence>
      {isPaused && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 z-50 flex items-center justify-center rounded-xl bg-background/80 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="Interview paused"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="flex flex-col items-center gap-4"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <PauseIcon className="h-8 w-8 text-muted-foreground" />
            </div>
            <h2 className="text-xl font-bold">Interview Paused</h2>
            <p className="text-sm text-muted-foreground">
              Take your time. Press resume when you&apos;re ready.
            </p>
            <Button type="button" size="lg" onClick={onResume} className="mt-2">
              <Play className="h-4 w-4" /> Resume
            </Button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
});
