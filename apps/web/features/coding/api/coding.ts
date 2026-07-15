import { api } from "@/lib/api/client";

export interface RunCodeInput {
  language: string;
  source_code: string;
  test_input?: string;
}

export interface RunCodeResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  execution_ms: number;
  timed_out: boolean;
}

export interface SubmissionResult {
  submission_id: string;
  status: string;
  language: string;
  passed_count: number;
  total_count: number;
  execution_ms: number | null;
  test_results: Array<{
    passed: boolean;
    is_hidden: boolean;
    actual_output: string | null;
  }>;
  compiler_output: string | null;
  stdout: string | null;
  stderr: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface LanguageInfo {
  id: string;
  name: string;
  extension: string;
}

export const codingApi = {
  run: (data: RunCodeInput) => api.post<RunCodeResult>("/code/run", data),

  submit: (data: { interview_id: string; language: string; source_code: string; test_inputs?: string[] }) =>
    api.post<SubmissionResult>("/code/submit", data),

  getResult: (id: string) => api.get<SubmissionResult>(`/code/result/${id}`),

  listLanguages: () => api.get<{ languages: LanguageInfo[] }>("/code/languages"),
};
