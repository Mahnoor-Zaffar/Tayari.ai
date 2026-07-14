import { useQuery } from "@tanstack/react-query";

import { analyticsApi } from "@/features/analytics/api/analytics";

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: () => analyticsApi.getAnalytics(),
    staleTime: 60_000,
  });
}
