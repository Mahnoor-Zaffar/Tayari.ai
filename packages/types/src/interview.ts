import { z } from "zod";

export const InterviewType = z.enum(["coding", "system-design", "behavioral"]);
export type InterviewType = z.infer<typeof InterviewType>;

export const ExperienceLevel = z.enum(["junior", "mid-senior", "staff-lead"]);
export type ExperienceLevel = z.infer<typeof ExperienceLevel>;

export const InterviewStatus = z.enum(["pending", "active", "completed", "cancelled"]);
export type InterviewStatus = z.infer<typeof InterviewStatus>;

export const ProgrammingLanguage = z.enum(["python", "java", "cpp", "javascript", "csharp"]);
export type ProgrammingLanguage = z.infer<typeof ProgrammingLanguage>;

export const Difficulty = z.enum(["easy", "medium", "hard"]);
export type Difficulty = z.infer<typeof Difficulty>;

export const Framework = z.enum([
  "react",
  "vue",
  "angular",
  "svelte",
  "django",
  "fastapi",
  "spring",
  "express",
  "next",
]);
export type Framework = z.infer<typeof Framework>;

export const DurationMinutes = z.union([z.literal(15), z.literal(30), z.literal(45)]);
export type DurationMinutes = z.infer<typeof DurationMinutes>;

export const CreateInterviewSchema = z
  .object({
    type: InterviewType,
    company: z.string().min(1, "Company is required").max(100),
    role: z.string().min(1, "Role is required").max(100),
    experience_level: ExperienceLevel,
    language: ProgrammingLanguage.nullable().optional(),
    framework: Framework.nullable().optional(),
    difficulty: Difficulty.default("medium"),
    duration_minutes: DurationMinutes.default(30),
    custom_instructions: z.string().max(2000).optional(),
    resume_id: z.string().uuid().nullable().optional(),
    job_description_id: z.string().uuid().nullable().optional(),
    template_id: z.string().uuid().nullable().optional(),
    device_checks: z.record(z.boolean()).default({}),
  })
  .refine((data) => data.type !== "coding" || !!data.language, {
    message: "language is required for coding interviews",
    path: ["language"],
  });

export type CreateInterviewInput = z.infer<typeof CreateInterviewSchema>;

export const InterviewSchema = z.object({
  id: z.string().uuid(),
  type: InterviewType,
  company: z.string(),
  role: z.string(),
  experience_level: ExperienceLevel,
  language: ProgrammingLanguage.nullable(),
  framework: Framework.nullable(),
  difficulty: Difficulty,
  duration_minutes: z.number(),
  custom_instructions: z.string().nullable(),
  status: InterviewStatus,
  timer_remaining: z.number(),
  resume_id: z.string().uuid().nullable(),
  job_description_id: z.string().uuid().nullable(),
  template_id: z.string().uuid().nullable(),
  created_at: z.string().datetime(),
});
export type Interview = z.infer<typeof InterviewSchema>;

export const ResumeUploadSchema = z.object({
  original_filename: z.string().min(1).max(255),
  mime_type: z.string(),
  file_size: z
    .number()
    .positive()
    .max(5 * 1024 * 1024),
  file_hash: z.string().min(32).max(64),
});
export type ResumeUploadInput = z.infer<typeof ResumeUploadSchema>;

export const ResumeResponseSchema = z.object({
  id: z.string().uuid(),
  original_filename: z.string(),
  mime_type: z.string(),
  file_size: z.number(),
  file_hash: z.string(),
  created_at: z.string().datetime(),
});
export type ResumeResponse = z.infer<typeof ResumeResponseSchema>;

export const JobDescriptionUploadSchema = z
  .object({
    source: z.enum(["text", "file"]).default("text"),
    raw_text: z.string().max(10000).optional(),
    original_filename: z.string().max(255).optional(),
    mime_type: z.string().optional(),
    file_size: z
      .number()
      .positive()
      .max(5 * 1024 * 1024)
      .optional(),
    file_hash: z.string().min(32).max(64).optional(),
  })
  .refine((data) => data.source !== "text" || (!!data.raw_text && data.raw_text.length > 0), {
    message: "raw_text is required when source is text",
    path: ["raw_text"],
  })
  .refine((data) => data.source !== "file" || !!data.file_hash, {
    message: "file_hash is required when source is file",
    path: ["file_hash"],
  });
export type JobDescriptionUploadInput = z.infer<typeof JobDescriptionUploadSchema>;

export const JobDescriptionResponseSchema = z.object({
  id: z.string().uuid(),
  source: z.string(),
  original_filename: z.string(),
  created_at: z.string().datetime(),
});
export type JobDescriptionResponse = z.infer<typeof JobDescriptionResponseSchema>;

export const DeviceCheckSchema = z.object({
  microphone: z.boolean(),
  camera: z.boolean(),
  speaker: z.boolean(),
  browser: z.boolean(),
});
export type DeviceCheckInput = z.infer<typeof DeviceCheckSchema>;

export const DeviceCheckResponseSchema = z.object({
  microphone: z.boolean(),
  camera: z.boolean(),
  speaker: z.boolean(),
  browser: z.boolean(),
  all_passed: z.boolean(),
});
export type DeviceCheckResponse = z.infer<typeof DeviceCheckResponseSchema>;

export const InterviewOptionsSchema = z.object({
  interview_types: z.array(z.object({ value: z.string(), label: z.string() })),
  companies: z.array(z.string()),
  roles: z.array(z.string()),
  languages: z.array(z.object({ value: z.string(), label: z.string() })),
  frameworks: z.array(z.object({ value: z.string(), label: z.string() })),
  experience_levels: z.array(z.object({ value: z.string(), label: z.string() })),
  difficulties: z.array(z.object({ value: z.string(), label: z.string() })),
  durations: z.array(z.object({ value: z.string(), label: z.string() })),
});
export type InterviewOptions = z.infer<typeof InterviewOptionsSchema>;
