"use client";

import { useCallback, useEffect, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

import { useFocusTrap } from "@/hooks/use-focus-trap";
import { cn } from "@/lib/utils";

interface SheetProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: "left" | "right";
  className?: string;
  title?: string;
}

const sideVariants = {
  left: {
    initial: { x: "-100%" },
    animate: { x: 0 },
    exit: { x: "-100%" },
  },
  right: {
    initial: { x: "100%" },
    animate: { x: 0 },
    exit: { x: "100%" },
  },
};

export function Sheet({ open, onClose, children, side = "left", className, title }: SheetProps) {
  const ref = useFocusTrap(open);

  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (open) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, handleEscape]);

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-black/50"
            aria-hidden="true"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            ref={ref}
            role="dialog"
            aria-modal="true"
            aria-label={title}
            initial={sideVariants[side].initial}
            animate={sideVariants[side].animate}
            exit={sideVariants[side].exit}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className={cn(
              "absolute top-0 bottom-0 flex w-72 flex-col bg-background shadow-xl",
              side === "left" ? "left-0" : "right-0",
              className,
            )}
          >
            {title && (
              <div className="flex items-center justify-between border-b px-4 py-3">
                <h2 className="text-lg font-semibold">{title}</h2>
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-md p-1 hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  aria-label="Close"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            )}
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
