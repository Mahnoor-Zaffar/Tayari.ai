import { useQuery, useMutation } from "@tanstack/react-query";
import { interviewSetupApi } from "@/features/interview/api/interview-setup";
import type {
  InterviewOptions,
  InterviewResponse,
  ResumeUploadResult,
  JobDescriptionUploadResult,
  DeviceCheckResult,
} from "@/features/interview/types";
import type {
  TemplateData,
  ParseResult,
  AnalyzeResult,
  DifficultyEstimate,
  ValidationResult,
} from "@/features/interview/api/interview-setup";

export function useInterviewOptions() {
  return useQuery({
    queryKey: ["interview", "options"],
    queryFn: () => interviewSetupApi.getOptions(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateInterview() {
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => interviewSetupApi.createInterview(data),
  });
}

export function useUploadResume() {
  return useMutation<
    ResumeUploadResult,
    Error,
    { original_filename: string; mime_type: string; file_size: number; file_hash: string }
  >({
    mutationFn: (data) => interviewSetupApi.uploadResume(data),
  });
}

export function useUploadJobDescription() {
  return useMutation<
    JobDescriptionUploadResult,
    Error,
    {
      source: "text" | "file";
      raw_text?: string;
      original_filename?: string;
      mime_type?: string;
      file_size?: number;
      file_hash?: string;
    }
  >({
    mutationFn: (data) => interviewSetupApi.uploadJobDescription(data),
  });
}

export function useDeviceCheck() {
  return useMutation<
    DeviceCheckResult,
    Error,
    { microphone: boolean; camera: boolean; speaker: boolean; browser: boolean }
  >({
    mutationFn: (data) => interviewSetupApi.deviceCheck(data),
  });
}

export function useInterviews() {
  return useQuery({
    queryKey: ["interview", "list"],
    queryFn: () => interviewSetupApi.list(),
    staleTime: 30_000,
  });
}

// ── Templates ───────────────────────────────────────────────────────────────

export function useTemplates() {
  return useQuery({
    queryKey: ["interview", "templates"],
    queryFn: () => interviewSetupApi.listTemplates(),
    staleTime: 60_000,
  });
}

export function useCreateTemplate() {
  return useMutation({
    mutationFn: (data: TemplateData) => interviewSetupApi.createTemplate(data),
  });
}

export function useDeleteTemplate() {
  return useMutation({
    mutationFn: (id: string) => interviewSetupApi.deleteTemplate(id),
  });
}

// ── Resume Parsing ─────────────────────────────────────────────────────────

export function useParseResume() {
  return useMutation<ParseResult, Error, { resumeId: string }>({
    mutationFn: ({ resumeId }) => interviewSetupApi.parseResume(resumeId),
  });
}

// ── JD Analysis ─────────────────────────────────────────────────────────────

export function useAnalyzeJobDescription() {
  return useMutation<AnalyzeResult, Error, { jdId: string }>({
    mutationFn: ({ jdId }) => interviewSetupApi.analyzeJobDescription(jdId),
  });
}

// ── Difficulty Estimate ─────────────────────────────────────────────────────

export function useEstimateDifficulty() {
  return useMutation<
    DifficultyEstimate,
    Error,
    { company: string; role: string; experience_level: string; language?: string | null }
  >({
    mutationFn: (params) => interviewSetupApi.estimateDifficulty(params),
  });
}

// ── Config Validation ────────────────────────────────────────────────────────

export function useValidateConfig() {
  return useMutation<ValidationResult, Error, Record<string, unknown>>({
    mutationFn: (data) => interviewSetupApi.validateConfig(data),
  });
}

// ── Recent Configs ──────────────────────────────────────────────────────────

export function useRecentConfigs() {
  return useQuery({
    queryKey: ["interview", "recent"],
    queryFn: () => interviewSetupApi.getRecent(),
    staleTime: 30_000,
  });
}
