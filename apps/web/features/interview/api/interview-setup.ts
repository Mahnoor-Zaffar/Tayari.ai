import { api } from "@/lib/api/client";
import type {
  InterviewOptions,
  InterviewResponse,
  ResumeUploadResult,
  JobDescriptionUploadResult,
  DeviceCheckResult,
} from "@/features/interview/types";

export interface TemplateData {
  name: string;
  description?: string | null;
  interview_type: string;
  company: string;
  role: string;
  experience_level: string;
  language?: string | null;
  framework?: string | null;
  difficulty?: string;
  duration_minutes?: number;
  custom_instructions?: string | null;
  system_design_problem?: string | null;
  resume_id?: string | null;
  job_description_id?: string | null;
}

export interface TemplateResponse {
  id: string;
  name: string;
  description: string | null;
  interview_type: string;
  company: string;
  role: string;
  experience_level: string;
  language: string | null;
  framework: string | null;
  difficulty: string;
  duration_minutes: number;
  custom_instructions: string | null;
  system_design_problem: string | null;
  resume_id: string | null;
  job_description_id: string | null;
  created_at: string;
}

export interface ParseResult {
  id: string;
  original_filename: string;
  skills: Array<{ name: string; category: string; confidence: number }>;
  technologies: string[];
  suggested_language: string | null;
  suggested_role: string | null;
  years_of_experience: number;
}

export interface AnalyzeResult {
  id: string;
  source: string;
  skills: Array<{ name: string; category: string; confidence: number }>;
  technologies: string[];
  requirements: Array<{ text: string; category: string; importance: string }>;
  suggested_language: string | null;
  suggested_focus_areas: string[];
}

export interface DifficultyEstimate {
  overall: string;
  score: number;
  factors: Array<{ factor: string; detail: string }>;
  description: string;
}

export interface ValidationWarning {
  field: string;
  message: string;
  severity: string;
}

export interface ValidationResult {
  score: number;
  warnings: ValidationWarning[];
  is_ready: boolean;
}

export const interviewSetupApi = {
  getOptions: () => api.get<InterviewOptions>("/interviews/options"),

  createInterview: (data: Record<string, unknown>) =>
    api.post<InterviewResponse>("/interviews", data),

  uploadResume: (data: {
    original_filename: string;
    mime_type: string;
    file_size: number;
    file_hash: string;
  }) => api.post<ResumeUploadResult>("/interviews/upload-resume", data),

  uploadJobDescription: (data: {
    source: "text" | "file";
    raw_text?: string;
    original_filename?: string;
    mime_type?: string;
    file_size?: number;
    file_hash?: string;
  }) => api.post<JobDescriptionUploadResult>("/interviews/upload-job-description", data),

  deviceCheck: (data: {
    microphone: boolean;
    camera: boolean;
    speaker: boolean;
    browser: boolean;
  }) => api.post<DeviceCheckResult>("/interviews/device-check", data),

  list: () => api.get<{ interviews: InterviewResponse[] }>("/interviews"),

  get: (id: string) => api.get<InterviewResponse>(`/interviews/${id}`),

  // ── Templates ───────────────────────────────────────────────────────────

  createTemplate: (data: TemplateData) => api.post<TemplateResponse>("/interviews/templates", data),

  listTemplates: () => api.get<{ templates: TemplateResponse[] }>("/interviews/templates"),

  getTemplate: (id: string) => api.get<TemplateResponse>(`/interviews/templates/${id}`),

  deleteTemplate: (id: string) => api.delete(`/interviews/templates/${id}`),

  // ── Resume Parsing ─────────────────────────────────────────────────────

  parseResume: (resumeId: string) => api.post<ParseResult>(`/interviews/${resumeId}/parse`),

  // ── JD Analysis ────────────────────────────────────────────────────────

  analyzeJobDescription: (jdId: string) =>
    api.post<AnalyzeResult>(`/interviews/job-descriptions/${jdId}/analyze`),

  // ── Difficulty Estimate ────────────────────────────────────────────────

  estimateDifficulty: (params: {
    company: string;
    role: string;
    experience_level: string;
    language?: string | null;
  }) => {
    const sp = new URLSearchParams();
    sp.set("company", params.company);
    sp.set("role", params.role);
    sp.set("experience_level", params.experience_level);
    if (params.language) sp.set("language", params.language);
    return api.get<DifficultyEstimate>(`/interviews/difficulty-estimate?${sp.toString()}`);
  },

  // ── Config Validation ──────────────────────────────────────────────────

  validateConfig: (data: Record<string, unknown>) =>
    api.post<ValidationResult>("/interviews/validate", data),

  // ── Recent Configs ─────────────────────────────────────────────────────

  getRecent: () => api.get<{ recent: InterviewResponse[] }>("/interviews/recent"),

  // ── Session ─────────────────────────────────────────────────────────────

  startSession: (interviewId: string) =>
    api.post<{
      session_id: string;
      interview_id: string;
      status: string;
      initial_question: string;
    }>("/sessions", { interview_id: interviewId }),

  getSessionStatus: (sessionId: string) =>
    api.get<{ state: string; remaining_seconds: number }>(`/sessions/${sessionId}`),
};
