"use client";

import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { codingApi, type RunCodeResult, type SubmissionResult } from "@/features/coding/api/coding";

export function useCodeExecution(interviewId: string) {
  const [output, setOutput] = useState<RunCodeResult | null>(null);
  const [submission, setSubmission] = useState<SubmissionResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const runMutation = useMutation({
    mutationFn: (data: { language: string; source_code: string; test_input?: string }) =>
      codingApi.run(data),
    onMutate: () => setIsRunning(true),
    onSuccess: (data) => setOutput(data),
    onError: (err) => setOutput({ stdout: "", stderr: String(err), exit_code: 1, execution_ms: 0, timed_out: false }),
    onSettled: () => setIsRunning(false),
  });

  const submitMutation = useMutation({
    mutationFn: (data: { language: string; source_code: string }) =>
      codingApi.submit({ interview_id: interviewId, ...data }),
    onMutate: () => setIsSubmitting(true),
    onSuccess: (data) => setSubmission(data),
    onError: (err) => setSubmission({
      submission_id: "", status: "error", language: "", passed_count: 0, total_count: 0,
      execution_ms: null, test_results: [], compiler_output: null, stdout: null, stderr: String(err),
      created_at: null, completed_at: null,
    }),
    onSettled: () => setIsSubmitting(false),
  });

  const run = useCallback((language: string, source_code: string, test_input?: string) => {
    setOutput(null);
    runMutation.mutate({ language, source_code, test_input });
  }, [runMutation]);

  const submit = useCallback((language: string, source_code: string) => {
    setSubmission(null);
    submitMutation.mutate({ language, source_code });
  }, [submitMutation]);

  const clearOutput = useCallback(() => setOutput(null), []);

  return { output, submission, isRunning, isSubmitting, run, submit, clearOutput };
}
