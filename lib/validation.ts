import { z } from 'zod';

export const turnAudioPayloadSchema = z.object({
  audio: z.instanceof(Blob, { message: 'audio must be a Blob' }),
  sessionId: z.string().uuid('sessionId must be a valid UUID'),
  userId: z.string().uuid('userId must be a valid UUID'),
});

export const evaluateTurnPayloadSchema = z.object({
  turnId: z.string().uuid('turnId must be a valid UUID'),
  interviewerQuestion: z.string().min(1, 'interviewerQuestion is required'),
  candidateResponse: z.string().min(1, 'candidateResponse is required'),
});

export const shadowEvaluatorResponseSchema = z.object({
  technicalScore: z.number().int().min(1).max(10),
  communicationScore: z.number().int().min(1).max(10),
  starFrameworkCheck: z.boolean(),
  constructiveCritique: z.string().min(1),
});
