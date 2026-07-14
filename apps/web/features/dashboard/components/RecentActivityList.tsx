"use client";

import { memo } from "react";
import { Clock, Mic, type LucideIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { SkeletonActivityItem } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { SectionHeader } from "@/components/shared/SectionHeader";
import type { RecentInterview } from "@/features/dashboard/types";
import { cn } from "@/lib/utils";

const statusIcons: Record<string, LucideIcon> = {
  completed: Mic,
  pending: Clock,
  in_progress: Clock,
};

const statusLabels: Record<string, string> = {
  completed: "Completed",
  pending: "Scheduled",
  in_progress: "In Progress",
};

const statusBadgeVariants: Record<string, "success" | "warning" | "secondary"> = {
  completed: "success",
  in_progress: "warning",
  pending: "secondary",
};

interface RecentActivityListProps {
  interviews?: RecentInterview[];
  isLoading: boolean;
  className?: string;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function getScoreColor(score: number | null): string {
  if (score == null) return "text-muted-foreground";
  if (score >= 80) return "text-success";
  if (score >= 60) return "text-warning";
  return "text-red-500";
}

const RecentActivityListItem = memo(function RecentActivityListItem({
  interview,
}: {
  interview: RecentInterview;
}) {
  const Icon = statusIcons[interview.status] ?? Clock;
  return (
    <div className="flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-accent/50">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
        <Icon className="h-5 w-5 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium">
          {interview.company} — {interview.type}
        </p>
        <p className="text-xs text-muted-foreground">{formatDate(interview.created_at)}</p>
      </div>
      <div className="flex items-center gap-3">
        {interview.overall_score != null && (
          <span className={cn("text-sm font-semibold", getScoreColor(interview.overall_score))}>
            {Math.round(interview.overall_score)}%
          </span>
        )}
        <Badge variant={statusBadgeVariants[interview.status] ?? "secondary"}>
          {statusLabels[interview.status] ?? interview.status}
        </Badge>
      </div>
    </div>
  );
});

export const RecentActivityList = memo(function RecentActivityList({
  interviews,
  isLoading,
  className,
}: RecentActivityListProps) {
  return (
    <section className={cn("space-y-3", className)}>
      <SectionHeader title="Recent Activity" description="Your latest interview sessions" />

      {isLoading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <SkeletonActivityItem key={i} />
          ))}
        </div>
      ) : !interviews || interviews.length === 0 ? (
        <EmptyState
          icon={Mic}
          title="No interviews yet"
          description="Start your first interview to see activity here."
        />
      ) : (
        <div className="space-y-2">
          {interviews.map((interview) => (
            <RecentActivityListItem key={interview.id} interview={interview} />
          ))}
        </div>
      )}
    </section>
  );
});
