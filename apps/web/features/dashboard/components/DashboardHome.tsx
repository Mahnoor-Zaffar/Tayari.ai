"use client";

import { AlertCircle, RefreshCw } from "lucide-react";

import { useDashboard, useRecentInterviews } from "@/features/dashboard/hooks/use-dashboard";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { StatsGrid } from "@/features/dashboard/components/StatsGrid";
import { RecentActivityList } from "@/features/dashboard/components/RecentActivityList";
import { QuickActions } from "@/features/dashboard/components/QuickActions";
import { WelcomeCard } from "@/features/dashboard/components/WelcomeCard";
import { SubscriptionStatus } from "@/features/dashboard/components/SubscriptionStatus";
import { InterviewProgress } from "@/features/dashboard/components/InterviewProgress";
import { Button } from "@/components/ui/button";
import { WidgetErrorBoundary } from "@/components/error/WidgetErrorBoundary";
import { getErrorMessage } from "@/lib/errors";

export function DashboardHome() {
  const { user } = useAuth();
  const {
    data: dashboard,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useDashboard();
  const {
    data: recentData,
    isLoading: recentLoading,
    error: recentError,
    refetch: refetchRecent,
  } = useRecentInterviews();

  if (summaryError || recentError) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16" role="alert">
        <div className="rounded-full bg-destructive/10 p-3">
          <AlertCircle className="h-6 w-6 text-destructive" />
        </div>
        <p className="text-lg font-medium">Failed to load dashboard</p>
        <p className="max-w-md text-center text-sm text-muted-foreground">
          {getErrorMessage(summaryError ?? recentError)}
        </p>
        <Button
          variant="outline"
          onClick={() => {
            refetchSummary();
            refetchRecent();
          }}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Try again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <WidgetErrorBoundary title="Welcome">
        <WelcomeCard
          displayName={user?.display_name}
          isLoading={summaryLoading}
          streak={dashboard?.stats.current_streak}
        />
      </WidgetErrorBoundary>

      <WidgetErrorBoundary title="Stats">
        <StatsGrid stats={dashboard?.stats} isLoading={summaryLoading} />
      </WidgetErrorBoundary>

      <WidgetErrorBoundary title="Quick Actions">
        <QuickActions />
      </WidgetErrorBoundary>

      <div className="grid gap-6 lg:grid-cols-3">
        <WidgetErrorBoundary title="Recent Activity">
          <RecentActivityList
            interviews={recentData?.interviews}
            isLoading={recentLoading}
            className="lg:col-span-2"
          />
        </WidgetErrorBoundary>
        <div className="space-y-6">
          <WidgetErrorBoundary title="Subscription">
            <SubscriptionStatus subscription={dashboard?.subscription} isLoading={summaryLoading} />
          </WidgetErrorBoundary>
          <WidgetErrorBoundary title="Interview Progress">
            <InterviewProgress
              latestReport={dashboard?.latest_report}
              completed={dashboard?.stats.completed_interviews}
              total={dashboard?.stats.total_interviews}
              isLoading={summaryLoading}
            />
          </WidgetErrorBoundary>
        </div>
      </div>
    </div>
  );
}
