"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { evaluationApi } from "@/features/evaluation/api/evaluation";

export function useEvaluation(interviewId: string) {
  const queryClient = useQueryClient();

  const evaluationQuery = useQuery({
    queryKey: ["evaluation", interviewId],
    queryFn: () => evaluationApi.getEvaluation(interviewId),
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes("404")) return false;
      return failureCount < 2;
    },
    staleTime: 60_000,
  });

  const interviewQuery = useQuery({
    queryKey: ["interview", interviewId],
    queryFn: () => evaluationApi.getInterview(interviewId),
    retry: 2,
    staleTime: 300_000,
  });

  const triggerMutation = useMutation({
    mutationFn: () => evaluationApi.triggerEvaluation(interviewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluation", interviewId] });
    },
  });

  const isNotFound =
    evaluationQuery.isError &&
    evaluationQuery.error instanceof Error &&
    evaluationQuery.error.message.includes("404");

  return {
    evaluation: evaluationQuery.data,
    interview: interviewQuery.data,
    isLoading: evaluationQuery.isLoading || interviewQuery.isLoading,
    isError: evaluationQuery.isError || interviewQuery.isError,
    isNotFound,
    error: evaluationQuery.error || interviewQuery.error,
    refetch: () => {
      evaluationQuery.refetch();
      interviewQuery.refetch();
    },
    triggerEvaluation: triggerMutation.mutateAsync,
    isTriggering: triggerMutation.isPending,
    triggerError: triggerMutation.error,
  };
}
