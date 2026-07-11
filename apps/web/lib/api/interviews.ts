import { api } from "./client"
import type { CreateInterviewInput, Interview, Evaluation } from "@tayari/types"

export const interviewsApi = {
  create: (data: CreateInterviewInput) => api.post<Interview>("/interviews", data),
  list: () => api.get<Interview[]>("/interviews"),
  get: (id: string) => api.get<Interview>(`/interviews/${id}`),
  getEvaluation: (id: string) => api.get<Evaluation>(`/interviews/${id}/evaluation`),
  generateEvaluation: (id: string) => api.post<Evaluation>(`/interviews/${id}/evaluation`),
}
