import { api } from "@/lib/api/client";
import type { DashboardData, RecentInterview } from "@/features/dashboard/types";

export const dashboardApi = {
  getDashboard: () => api.get<DashboardData>("/dashboard"),

  getRecentInterviews: () => api.get<{ interviews: RecentInterview[] }>("/dashboard/recent"),
};
