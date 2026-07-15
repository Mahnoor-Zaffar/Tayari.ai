import { api } from "@/lib/api/client";

export interface DimensionData {
  key: string;
  label: string;
  score: number;
  evidence: string;
}

export interface EvaluationData {
  evaluation_id: string;
  interview_id: string;
  overall_score: number;
  overall_score_100: number;
  hire_verdict: string;
  dimensions: DimensionData[];
  strengths: string[];
  improvements: string[];
  recommendations: string[];
  confidence: number;
}

export interface InterviewData {
  id: string;
  type: string;
  company: string;
  role: string;
  experience_level: string;
  language: string | null;
  difficulty: string;
  duration_minutes: number;
  status: string;
  created_at: string;
  transcript: Array<{ speaker: string; text: string; timestamp_ms: number }>;
}

export const evaluationApi = {
  getEvaluation: (interviewId: string) =>
    api.get<EvaluationData>(`/evaluations/${interviewId}`),

  triggerEvaluation: (interviewId: string) =>
    api.post<EvaluationData>(`/evaluations/${interviewId}`),

  getInterview: (interviewId: string) =>
    api.get<InterviewData>(`/interviews/${interviewId}`),
};
