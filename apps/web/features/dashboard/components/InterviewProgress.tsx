"use client";

import { memo } from "react";
import { BarChart3 } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { ProgressCard } from "@/components/shared/ProgressCard";
import type { LatestReport } from "@/features/dashboard/types";
import { cn } from "@/lib/utils";

interface InterviewProgressProps {
  latestReport?: LatestReport | null;
  completed?: number;
  total?: number;
  isLoading: boolean;
  className?: string;
}

const verdictLabels: Record<string, string> = {
  strong_hire: "Strong Hire — Excellent performance across all dimensions",
  hire: "Hire — Good performance with minor areas to improve",
  no_hire: "No Hire — Needs significant improvement",
};

export const InterviewProgress = memo(function InterviewProgress({
  latestReport,
  completed = 0,
  total = 0,
  isLoading,
  className,
}: InterviewProgressProps) {
  return (
    <div className={cn("rounded-xl border bg-card p-5 shadow-sm", className)}>
      <div className="mb-4 flex items-center gap-3">
        <div className="rounded-lg bg-muted p-2.5">
          <BarChart3 className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <p className="text-sm font-medium">Interview Progress</p>
          <p className="text-xs text-muted-foreground">Your performance overview</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-4 w-24" />
        </div>
      ) : total > 0 ? (
        <div className="space-y-4">
          <ProgressCard label="Completed" value={completed} max={total} color="success" />
          {latestReport && (
            <div className="space-y-1.5">
              <p className="text-sm font-medium">Latest Evaluation</p>
              <p className="text-2xl font-bold">
                {latestReport.overall_score != null
                  ? `${Math.round(latestReport.overall_score)}%`
                  : "—"}
              </p>
              {latestReport.hire_verdict && (
                <p className="text-xs text-muted-foreground">
                  {verdictLabels[latestReport.hire_verdict] ?? latestReport.hire_verdict}
                </p>
              )}
            </div>
          )}
        </div>
      ) : (
        <EmptyState
          icon={BarChart3}
          title="No interviews yet"
          description="Complete an interview to see your progress."
        />
      )}
    </div>
  );
});
