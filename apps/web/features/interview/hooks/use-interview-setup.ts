import { useQuery, useMutation } from "@tanstack/react-query";
import { interviewSetupApi } from "@/features/interview/api/interview-setup";
import type {
  InterviewOptions,
  InterviewResponse,
  ResumeUploadResult,
  JobDescriptionUploadResult,
  DeviceCheckResult,
} from "@/features/interview/types";

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
