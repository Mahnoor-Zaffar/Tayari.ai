"use client";

import { memo } from "react";
import { Brain, Calendar, Flame, Star } from "lucide-react";

import { SkeletonStatCard } from "@/components/ui/skeleton";
import { StatCard } from "@/components/shared/StatCard";
import type { DashboardStats } from "@/features/dashboard/types";
import { cn } from "@/lib/utils";

interface StatsGridProps {
  stats?: DashboardStats;
  isLoading: boolean;
  className?: string;
}

const skeletonIds = ["stat-1", "stat-2", "stat-3", "stat-4"];

export const StatsGrid = memo(function StatsGrid({ stats, isLoading, className }: StatsGridProps) {
  if (isLoading) {
    return (
      <div className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-4", className)}>
        {skeletonIds.map((id) => (
          <SkeletonStatCard key={id} />
        ))}
      </div>
    );
  }

  return (
    <div className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-4", className)}>
      <StatCard
        title="Total Interviews"
        value={stats?.total_interviews ?? 0}
        icon={Calendar}
        description="All time interviews"
      />
      <StatCard
        title="Completed"
        value={stats?.completed_interviews ?? 0}
        icon={Brain}
        variant="success"
        description={`${stats?.active_interviews ?? 0} active in progress`}
      />
      <StatCard
        title="Current Streak"
        value={stats?.current_streak ?? 0}
        icon={Flame}
        variant="warning"
        description={
          stats?.current_streak
            ? `${stats.current_streak} day${stats.current_streak > 1 ? "s" : ""} streak!`
            : "No active streak"
        }
      />
      <StatCard
        title="Average Score"
        value={stats?.average_score != null ? `${Math.round(stats.average_score)}%` : "—"}
        icon={Star}
        variant="primary"
        description={stats?.average_score != null ? "Across all evaluations" : "No scores yet"}
      />
    </div>
  );
});
