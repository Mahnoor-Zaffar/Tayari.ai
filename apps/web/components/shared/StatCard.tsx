"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: { value: number; positive: boolean };
  variant?: "default" | "primary" | "success" | "warning";
  className?: string;
}

const variantStyles = {
  default: "bg-card",
  primary: "bg-primary text-primary-foreground",
  success: "bg-success-bg border-success-border",
  warning: "bg-warning-bg border-warning-border",
};

const iconStyles = {
  default: "text-muted-foreground",
  primary: "text-primary-foreground",
  success: "text-success",
  warning: "text-warning",
};

export const StatCard = memo(function StatCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  variant = "default",
  className,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "rounded-xl border p-5 shadow-sm transition-shadow hover:shadow-md",
        variantStyles[variant],
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p
            className={cn(
              "text-sm font-medium",
              variant === "primary" ? "text-primary-foreground/80" : "text-muted-foreground",
            )}
          >
            {title}
          </p>
          <p
            className={cn(
              "text-2xl font-bold tracking-tight",
              variant === "primary" && "text-primary-foreground",
            )}
          >
            {typeof value === "number" ? value.toLocaleString() : value}
          </p>
          {description && (
            <p
              className={cn(
                "text-xs",
                variant === "primary" ? "text-primary-foreground/70" : "text-muted-foreground",
              )}
            >
              {description}
            </p>
          )}
          {trend && (
            <p
              className={cn(
                "text-xs font-medium",
                trend.positive ? "text-emerald-600" : "text-red-500",
              )}
            >
              {trend.positive ? "+" : ""}
              {trend.value}% from last month
            </p>
          )}
        </div>
        <div
          className={cn(
            "rounded-lg p-2.5",
            variant === "default" ? "bg-muted" : "bg-background/20",
          )}
        >
          <Icon className={cn("h-5 w-5", iconStyles[variant])} />
        </div>
      </div>
    </motion.div>
  );
});
