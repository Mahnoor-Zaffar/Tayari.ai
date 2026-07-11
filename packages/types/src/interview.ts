import { z } from "zod"

export const InterviewType = z.enum(["coding", "system-design", "behavioral"])
export type InterviewType = z.infer<typeof InterviewType>

export const ExperienceLevel = z.enum(["junior", "mid-senior", "staff-lead"])
export type ExperienceLevel = z.infer<typeof ExperienceLevel>

export const InterviewStatus = z.enum(["pending", "active", "completed", "cancelled"])
export type InterviewStatus = z.infer<typeof InterviewStatus>

export const ProgrammingLanguage = z.enum(["python", "java", "cpp", "javascript", "csharp"])
export type ProgrammingLanguage = z.infer<typeof ProgrammingLanguage>

export const CreateInterviewSchema = z.object({
  type: InterviewType,
  company: z.string().min(1, "Company is required"),
  experienceLevel: ExperienceLevel,
  language: ProgrammingLanguage.optional(),
})

export type CreateInterviewInput = z.infer<typeof CreateInterviewSchema>

export const InterviewSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  type: InterviewType,
  company: z.string(),
  experienceLevel: ExperienceLevel,
  language: ProgrammingLanguage.nullable(),
  status: InterviewStatus,
  timerRemaining: z.number(),
  createdAt: z.string().datetime(),
  startedAt: z.string().datetime().nullable(),
  completedAt: z.string().datetime().nullable(),
})

export type Interview = z.infer<typeof InterviewSchema>
