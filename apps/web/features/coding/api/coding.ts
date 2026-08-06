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

export interface ProblemSummary {
  id: string;
  slug: string;
  title: string;
  difficulty: string;
}

export interface ProblemExample {
  input: string;
  output: string;
  explanation?: string | null;
}

export interface ProblemTestCase {
  id: string;
  input: string;
  expected_output: string;
}

export interface ProblemDetail extends ProblemSummary {
  description: string;
  examples: ProblemExample[];
  constraints: string[];
  test_cases: ProblemTestCase[];
  total_test_count: number;
  hidden_test_count: number;
}

export const codingApi = {
  run: (data: RunCodeInput) => api.post<RunCodeResult>("/code/run", data),

  submit: (data: {
    interview_id: string;
    language: string;
    source_code: string;
    test_inputs?: string[];
    problem_id?: string;
  }) => api.post<SubmissionResult>("/code/submit", data),

  getResult: (id: string) => api.get<SubmissionResult>(`/code/result/${id}`),

  listLanguages: () => api.get<{ languages: LanguageInfo[] }>("/code/languages"),

  listProblems: () => api.get<{ problems: ProblemSummary[] }>("/code/problems"),

  getProblem: (id: string) => api.get<ProblemDetail>(`/code/problems/${id}`),
};
