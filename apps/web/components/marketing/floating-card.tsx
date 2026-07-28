"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface FloatingCardProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  x?: number;
  y?: number;
  rotate?: number;
}

export function FloatingCard({
  children,
  className,
  delay = 0,
  x = 0,
  y = -20,
  rotate = 0,
}: FloatingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: [y, -y, y] }}
      transition={{
        opacity: { duration: 0.6, delay },
        y: { duration: 6, repeat: Infinity, ease: "easeInOut", delay },
      }}
      style={{ rotate }}
      className={cn(
        "absolute rounded-xl border border-white/10 bg-card/80 p-4 shadow-2xl shadow-black/20 backdrop-blur-xl",
        className,
      )}
    >
      {children}
    </motion.div>
  );
}
