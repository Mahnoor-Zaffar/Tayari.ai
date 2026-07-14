import { api } from "@/lib/api/client";
import type {
  InterviewOptions,
  InterviewResponse,
  ResumeUploadResult,
  JobDescriptionUploadResult,
  DeviceCheckResult,
} from "@/features/interview/types";

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
};
