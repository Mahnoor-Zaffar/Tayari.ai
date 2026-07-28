import type { Metadata } from "next";
import { AnalyticsDashboard } from "@/features/analytics/components/AnalyticsDashboard";
import { PageHeader } from "@/components/shared/PageHeader";

export const metadata: Metadata = {
  title: "Analytics — Tayari AI",
  description: "Interview activity and performance trends",
};

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        description="Track your interview activity and performance over time"
      />
      <AnalyticsDashboard />
    </div>
  );
}
