import { api } from "@/lib/api/client";

export interface EvaluationSummary {
  id: string;
  interview_id: string;
  overall_score: number | null;
  hire_verdict: string | null;
  dimensions: Record<string, unknown>;
  strengths: string[];
  improvements: string[];
  status: string;
  created_at: string | null;
}

export const reportsApi = {
  listEvaluations: () => api.get<{ evaluations: EvaluationSummary[] }>("/evaluations"),
};
