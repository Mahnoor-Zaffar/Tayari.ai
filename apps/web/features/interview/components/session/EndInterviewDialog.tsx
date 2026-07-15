"use client";

import { memo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EndInterviewDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const EndInterviewDialog = memo(function EndInterviewDialog({
  isOpen,
  onClose,
  onConfirm,
}: EndInterviewDialogProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/60 backdrop-blur-sm"
          onClick={onClose}
          role="dialog"
          aria-modal="true"
          aria-label="End interview confirmation"
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="mx-4 w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-lg"
          >
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <h3 className="font-semibold">End Interview?</h3>
                <p className="text-sm text-muted-foreground">
                  Your progress will be saved and you&apos;ll receive an evaluation.
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="ml-auto"
                onClick={onClose}
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1 border-destructive/30 text-destructive hover:bg-destructive/10"
                onClick={onConfirm}
              >
                <LogOut className="h-4 w-4" /> End Interview
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
});
