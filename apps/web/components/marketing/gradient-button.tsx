"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface GradientButtonProps {
  href: string;
  children: React.ReactNode;
  variant?: "primary" | "outline";
  size?: "default" | "lg";
  className?: string;
}

export function GradientButton({
  href,
  children,
  variant = "primary",
  size = "default",
  className,
}: GradientButtonProps) {
  return (
    <Link href={href}>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={cn(
          "relative inline-flex items-center justify-center rounded-xl font-medium transition-all",
          size === "lg" ? "h-12 px-8 text-base" : "h-10 px-6 text-sm",
          variant === "primary" &&
            "bg-gradient-to-r from-primary to-purple-600 text-white shadow-lg shadow-primary/25 hover:shadow-primary/40",
          variant === "outline" &&
            "border border-white/10 bg-white/5 text-foreground backdrop-blur-sm hover:bg-white/10",
          className,
        )}
      >
        {children}
      </motion.button>
    </Link>
  );
}
