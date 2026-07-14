import { useQuery } from "@tanstack/react-query";

import { dashboardApi } from "@/features/dashboard/api/dashboard";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => dashboardApi.getDashboard(),
    staleTime: 30_000,
  });
}

export function useRecentInterviews() {
  return useQuery({
    queryKey: ["dashboard", "recent"],
    queryFn: () => dashboardApi.getRecentInterviews(),
    staleTime: 15_000,
  });
}

export function useAnalytics() {
  return useQuery({
    queryKey: ["dashboard", "analytics"],
    queryFn: () => dashboardApi.getAnalytics(),
    staleTime: 60_000,
  });
}
