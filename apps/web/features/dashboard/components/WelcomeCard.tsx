"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

import { SkeletonLine } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface WelcomeCardProps {
  displayName?: string;
  isLoading: boolean;
  streak?: number;
  className?: string;
}

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function getTip(streak?: number): string {
  if (!streak || streak === 0) return "Complete your first interview to start a streak!";
  if (streak < 3) return "You're building momentum — keep going!";
  if (streak < 7) return `${streak}-day streak! You're on fire!`;
  return `Amazing ${streak}-day streak! You're unstoppable!`;
}

export const WelcomeCard = memo(function WelcomeCard({
  displayName,
  isLoading,
  streak,
  className,
}: WelcomeCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative overflow-hidden rounded-xl bg-gradient-to-br from-primary via-primary/90 to-primary/80 p-6 text-primary-foreground shadow-lg",
        className,
      )}
    >
      {/* Decorative background */}
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-primary-foreground/10" />
      <div className="absolute -bottom-4 -left-4 h-16 w-16 rounded-full bg-primary-foreground/5" />

      <div className="relative space-y-1.5">
        {isLoading ? (
          <div className="space-y-2">
            <SkeletonLine width="w-48" className="bg-primary-foreground/20 h-6" />
            <SkeletonLine width="w-36" className="bg-primary-foreground/20" />
            <SkeletonLine width="w-64" className="bg-primary-foreground/20" />
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold">
                {greeting()}, {displayName ?? "there"}!
              </h2>
              <Sparkles className="h-5 w-5 text-yellow-300" />
            </div>
            <p className="text-sm text-primary-foreground/80">Ready for your next interview?</p>
            <p className="text-xs text-primary-foreground/60">{getTip(streak)}</p>
          </>
        )}
      </div>
    </motion.div>
  );
});
