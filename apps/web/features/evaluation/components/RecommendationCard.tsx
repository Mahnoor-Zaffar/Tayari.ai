"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { BookOpen, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface RecommendationCardProps {
  recommendations: string[];
  className?: string;
}

export const RecommendationCard = memo(function RecommendationCard({
  recommendations, className,
}: RecommendationCardProps) {
  if (recommendations.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className={cn("rounded-lg border border-border bg-card p-4", className)}
    >
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        <BookOpen className="h-4 w-4 text-primary" /> Recommended Focus Areas
      </h3>
      <ul className="mt-3 space-y-2">
        {recommendations.map((r, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
            <span>{r}</span>
          </li>
        ))}
      </ul>
    </motion.div>
  );
});
