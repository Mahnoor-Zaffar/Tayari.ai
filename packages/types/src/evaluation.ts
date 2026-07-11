import { z } from "zod"

export const HireVerdict = z.enum(["hire", "lean-hire", "lean-no-hire", "no-hire"])
export type HireVerdict = z.infer<typeof HireVerdict>

export const DimensionScoreSchema = z.object({
  score: z.number().min(1).max(5),
  evidence: z.string(),
})

export const EvaluationSchema = z.object({
  id: z.string().uuid(),
  interviewId: z.string().uuid(),
  overallScore: z.number().min(1).max(5),
  dimensions: z.record(DimensionScoreSchema),
  hireVerdict: HireVerdict,
  strengths: z.array(z.string()),
  improvements: z.array(z.string()),
  deltaVsLast: z.number().nullable(),
  status: z.enum(["pending", "generating", "complete", "failed"]),
  createdAt: z.string().datetime(),
})

export type Evaluation = z.infer<typeof EvaluationSchema>
