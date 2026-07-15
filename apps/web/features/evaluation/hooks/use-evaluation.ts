"use client";

import { useQuery } from "@tanstack/react-query";
import { evaluationApi } from "@/features/evaluation/api/evaluation";

export function useEvaluation(interviewId: string) {
  const evaluationQuery = useQuery({
    queryKey: ["evaluation", interviewId],
    queryFn: () => evaluationApi.getEvaluation(interviewId),
    retry: 2,
    staleTime: 60_000,
  });

  const interviewQuery = useQuery({
    queryKey: ["interview", interviewId],
    queryFn: () => evaluationApi.getInterview(interviewId),
    retry: 2,
    staleTime: 300_000,
  });

  return {
    evaluation: evaluationQuery.data,
    interview: interviewQuery.data,
    isLoading: evaluationQuery.isLoading || interviewQuery.isLoading,
    isError: evaluationQuery.isError || interviewQuery.isError,
    error: evaluationQuery.error || interviewQuery.error,
    refetch: () => {
      evaluationQuery.refetch();
      interviewQuery.refetch();
    },
  };
}
