"use client";

import { memo, useMemo } from "react";
import { BarChart, TrendingUp, CalendarDays, Brain } from "lucide-react";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { StatCard } from "@/components/shared/StatCard";
import { SkeletonStatCard, SkeletonWidgetCard } from "@/components/ui/skeleton";
import { useAnalytics } from "@/features/analytics/hooks/use-analytics";
import { cn } from "@/lib/utils";
import type { AnalyticsDatapoint } from "@/features/analytics/types";

interface AnalyticsDashboardProps {
  className?: string;
}

export const AnalyticsDashboard = memo(function AnalyticsDashboard({
  className,
}: AnalyticsDashboardProps) {
  const { data, isLoading, error } = useAnalytics();

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16" role="alert">
        <p className="text-lg font-medium">Failed to load analytics</p>
        <p className="text-sm text-muted-foreground">Please try again later.</p>
      </div>
    );
  }

  const allData = useMemo(() => {
    if (!data) return null;
    return {
      daily: data.daily ?? [],
      weekly: data.weekly ?? [],
      monthly: data.monthly ?? [],
    };
  }, [data]);

  const totals = useMemo(() => {
    if (!allData) return null;
    const total = allData.monthly.reduce((s, d) => s + d.interviews, 0);
    const scores = allData.monthly.filter((d) => d.average_score != null);
    const avgScore = scores.length
      ? scores.reduce((s, d) => s + (d.average_score ?? 0), 0) / scores.length
      : null;
    return { totalInterviews: total, averageScore: avgScore };
  }, [allData]);

  return (
    <div className={cn("space-y-6", className)}>
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonStatCard key={i} />
          ))}
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Interviews"
              value={totals?.totalInterviews ?? 0}
              icon={BarChart}
              description="All completed interviews"
            />
            <StatCard
              title="Average Score"
              value={
                totals?.averageScore != null ? `${Math.round(totals.averageScore * 20)}%` : "\u2014"
              }
              icon={TrendingUp}
              variant="primary"
              description="Across all time"
            />
            <StatCard
              title="This Month"
              value={allData?.monthly?.at(-1)?.interviews ?? 0}
              icon={CalendarDays}
              description={`${allData?.monthly?.at(-1)?.interviews ?? 0} interviews this month`}
            />
            <StatCard
              title="Best Month"
              value={
                allData?.monthly?.length ? Math.max(...allData.monthly.map((d) => d.interviews)) : 0
              }
              icon={Brain}
              variant="success"
              description="Most interviews in a month"
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <ActivityChart
              title="Monthly Activity"
              data={allData?.monthly ?? []}
              isLoading={isLoading}
            />
            <ActivityChart
              title="Weekly Activity"
              data={allData?.weekly?.slice(-12) ?? []}
              isLoading={isLoading}
            />
          </div>
        </>
      )}

      {!isLoading &&
        !allData?.daily?.length &&
        !allData?.weekly?.length &&
        !allData?.monthly?.length && (
          <EmptyState
            icon={BarChart}
            title="No analytics data yet"
            description="Complete some interviews to see your activity trends."
          />
        )}
    </div>
  );
});

interface ActivityChartProps {
  title: string;
  data: AnalyticsDatapoint[];
  isLoading: boolean;
}

const ActivityChart = memo(function ActivityChart({ title, data, isLoading }: ActivityChartProps) {
  const maxValue = Math.max(1, ...data.map((d) => d.interviews));

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <SectionHeader title={title} />
      {isLoading ? (
        <SkeletonWidgetCard lines={4} className="border-0 p-0 shadow-none" />
      ) : data.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">No data yet</p>
      ) : (
        <div className="mt-4 flex items-end gap-1.5" style={{ height: 160 }}>
          {data.map((point) => {
            const height = (point.interviews / maxValue) * 140;
            return (
              <div
                key={point.period}
                className="group relative flex flex-1 flex-col items-center justify-end"
              >
                <div
                  className="w-full rounded-t bg-primary/60 transition-colors hover:bg-primary"
                  style={{ height: Math.max(4, height) }}
                  title={`${point.period}: ${point.interviews} interviews${
                    point.average_score != null
                      ? `, avg ${Math.round(point.average_score * 20)}%`
                      : ""
                  }`}
                />
                <span className="mt-1.5 text-[10px] text-muted-foreground">
                  {point.period.length > 7 ? point.period.slice(-2) : point.period.slice(-2)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
});
