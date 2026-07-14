import { api } from "@/lib/api/client";
import type { AnalyticsData } from "@/features/analytics/types";

export const analyticsApi = {
  getAnalytics: () => api.get<AnalyticsData>("/analytics"),
};
