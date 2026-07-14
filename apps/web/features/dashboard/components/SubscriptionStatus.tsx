"use client";

import { memo } from "react";
import { CreditCard } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import type { SubscriptionInfo } from "@/features/dashboard/types";
import { cn } from "@/lib/utils";

interface SubscriptionStatusProps {
  subscription?: SubscriptionInfo | null;
  isLoading: boolean;
  className?: string;
}

const planLabels: Record<string, string> = {
  free: "Free",
  pro: "Pro",
  enterprise: "Enterprise",
};

const planBadgeVariants: Record<string, "secondary" | "default" | "success"> = {
  free: "secondary",
  pro: "default",
  enterprise: "success",
};

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export const SubscriptionStatus = memo(function SubscriptionStatus({
  subscription,
  isLoading,
  className,
}: SubscriptionStatusProps) {
  return (
    <div className={cn("rounded-xl border bg-card p-5 shadow-sm", className)}>
      <div className="mb-4 flex items-center gap-3">
        <div className="rounded-lg bg-muted p-2.5">
          <CreditCard className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-medium">Subscription</p>
          <p className="text-xs text-muted-foreground">Your current plan</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
      ) : subscription ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold capitalize">
              {planLabels[subscription.plan ?? ""] ?? subscription.plan}
            </span>
            <Badge variant={planBadgeVariants[subscription.plan ?? ""] ?? "secondary"}>
              {subscription.status}
            </Badge>
          </div>
          {subscription.current_period_end && (
            <p className="text-xs text-muted-foreground">
              Renews {formatDate(subscription.current_period_end)}
            </p>
          )}
          <Button variant="outline" size="sm" className="w-full">
            Manage Plan
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">No active subscription</p>
          <Button variant="default" size="sm" className="w-full">
            Upgrade to Pro
          </Button>
        </div>
      )}
    </div>
  );
});
