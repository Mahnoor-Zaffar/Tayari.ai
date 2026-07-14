"use client";

import { memo, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface StepTransitionProps {
  step: number;
  children: ReactNode;
  className?: string;
}

export const StepTransition = memo(function StepTransition({
  step,
  children,
  className,
}: StepTransitionProps) {
  return (
    <div className={cn("relative overflow-hidden", className)}>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </div>
  );
});
