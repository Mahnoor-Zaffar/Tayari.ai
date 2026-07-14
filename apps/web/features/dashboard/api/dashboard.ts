import { api } from "@/lib/api/client";
import type { AnalyticsData, DashboardData, RecentInterview } from "@/features/dashboard/types";

export const dashboardApi = {
  getDashboard: () => api.get<DashboardData>("/dashboard"),

  getRecentInterviews: () => api.get<{ interviews: RecentInterview[] }>("/dashboard/recent"),

  getAnalytics: () => api.get<AnalyticsData>("/dashboard/analytics"),
};
