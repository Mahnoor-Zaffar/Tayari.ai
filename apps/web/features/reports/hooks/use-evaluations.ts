"use client";

import { useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/features/reports/api/reports";

export function useEvaluations() {
  return useQuery({
    queryKey: ["evaluations", "list"],
    queryFn: () => reportsApi.listEvaluations(),
    staleTime: 30_000,
  });
}
