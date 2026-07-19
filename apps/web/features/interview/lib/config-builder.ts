import type { InterviewSetupFormValues } from "./wizard-schema";
import type { InterviewOptions, InterviewResponse } from "@/features/interview/types";

export type InterviewDifficulty = "easy" | "medium" | "hard";

export type InterviewFramework =
  | "react"
  | "vue"
  | "angular"
  | "svelte"
  | "django"
  | "fastapi"
  | "spring"
  | "express"
  | "next"
  | null;

export type InterviewLanguage = "python" | "java" | "cpp" | "javascript" | "csharp" | null;

export type InterviewSeniorityLevel = "junior" | "mid-senior" | "staff-lead";

export type InterviewType = "coding" | "system-design" | "behavioral";

export type DeviceStatus = {
  microphone: boolean;
  camera: boolean;
  speaker: boolean;
  browser: boolean;
  network: "good" | "poor" | "offline" | "unknown";
};

export interface InterviewConfiguration {
  interview_type: InterviewType;
  company: string;
  role: string;
  seniority: InterviewSeniorityLevel;
  language: InterviewLanguage;
  framework: InterviewFramework;
  duration_minutes: number;
  difficulty: InterviewDifficulty;
  resume_reference: string | null;
  job_description_reference: string | null;
  template_reference: string | null;
  custom_prompt: string | null;
  device_status: DeviceStatus;
}

export function buildInterviewConfiguration(
  values: InterviewSetupFormValues,
): InterviewConfiguration {
  return {
    interview_type: values.type as InterviewType,
    company: values.company,
    role: values.role,
    seniority: values.experience_level as InterviewSeniorityLevel,
    language: (values.language || null) as InterviewLanguage,
    framework: (values.framework || null) as InterviewFramework,
    duration_minutes: values.duration_minutes,
    difficulty: values.difficulty as InterviewDifficulty,
    resume_reference: values.resume_id ?? null,
    job_description_reference: values.job_description_id ?? null,
    template_reference: values.template_id ?? null,
    custom_prompt: values.custom_instructions ?? null,
    device_status: {
      microphone: false,
      camera: false,
      speaker: false,
      browser: false,
      network: "unknown",
    },
  };
}

export function buildInterviewConfigurationFromResponse(
  response: InterviewResponse,
): InterviewConfiguration {
  return {
    interview_type: response.type as InterviewType,
    company: response.company,
    role: response.role,
    seniority: response.experience_level as InterviewSeniorityLevel,
    language: (response.language || null) as InterviewLanguage,
    framework: (response.framework || null) as InterviewFramework,
    duration_minutes: response.duration_minutes,
    difficulty: response.difficulty as InterviewDifficulty,
    resume_reference: response.resume_id ?? null,
    job_description_reference: response.job_description_id ?? null,
    template_reference: response.template_id ?? null,
    custom_prompt: response.custom_instructions ?? null,
    device_status: {
      microphone: false,
      camera: false,
      speaker: false,
      browser: false,
      network: "unknown",
    },
  };
}

export function resolveOptionLabel(
  options: InterviewOptions | undefined,
  category: keyof InterviewOptions,
  value: string | null | undefined,
): string {
  if (!value) return "\u2014";
  const list = options?.[category];
  if (!list) return value;
  if (Array.isArray(list) && list.length > 0 && typeof list[0] === "string") {
    return value;
  }
  const items = list as { value: string; label: string }[];
  return items.find((i) => i.value === value)?.label ?? value;
}
