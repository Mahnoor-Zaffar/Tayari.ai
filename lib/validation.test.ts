import { describe, it, expect } from 'vitest';
import {
  evaluateTurnPayloadSchema,
  shadowEvaluatorResponseSchema,
} from './validation';

describe('evaluateTurnPayloadSchema', () => {
  it('accepts valid payload', () => {
    const result = evaluateTurnPayloadSchema.safeParse({
      turnId: '550e8400-e29b-41d4-a716-446655440000',
      interviewerQuestion: 'Tell me about yourself?',
      candidateResponse: 'I worked at Google.',
    });
    expect(result.success).toBe(true);
  });

  it('rejects missing turnId', () => {
    const result = evaluateTurnPayloadSchema.safeParse({
      interviewerQuestion: 'Q?',
      candidateResponse: 'A.',
    });
    expect(result.success).toBe(false);
  });

  it('rejects non-UUID turnId', () => {
    const result = evaluateTurnPayloadSchema.safeParse({
      turnId: 'not-a-uuid',
      interviewerQuestion: 'Q?',
      candidateResponse: 'A.',
    });
    expect(result.success).toBe(false);
  });

  it('rejects empty interviewerQuestion', () => {
    const result = evaluateTurnPayloadSchema.safeParse({
      turnId: '550e8400-e29b-41d4-a716-446655440000',
      interviewerQuestion: '',
      candidateResponse: 'A.',
    });
    expect(result.success).toBe(false);
  });
});

describe('shadowEvaluatorResponseSchema', () => {
  it('accepts valid scores', () => {
    const result = shadowEvaluatorResponseSchema.safeParse({
      technicalScore: 7,
      communicationScore: 6,
      starFrameworkCheck: true,
      constructiveCritique: 'Good answer but lacking metrics.',
    });
    expect(result.success).toBe(true);
  });

  it('rejects technicalScore below 1', () => {
    const result = shadowEvaluatorResponseSchema.safeParse({
      technicalScore: 0,
      communicationScore: 5,
      starFrameworkCheck: false,
      constructiveCritique: 'Needs improvement.',
    });
    expect(result.success).toBe(false);
  });

  it('rejects technicalScore above 10', () => {
    const result = shadowEvaluatorResponseSchema.safeParse({
      technicalScore: 11,
      communicationScore: 5,
      starFrameworkCheck: false,
      constructiveCritique: 'Needs improvement.',
    });
    expect(result.success).toBe(false);
  });

  it('rejects non-boolean starFrameworkCheck', () => {
    const result = shadowEvaluatorResponseSchema.safeParse({
      technicalScore: 5,
      communicationScore: 5,
      starFrameworkCheck: 'yes',
      constructiveCritique: 'OK.',
    });
    expect(result.success).toBe(false);
  });

  it('rejects empty constructiveCritique', () => {
    const result = shadowEvaluatorResponseSchema.safeParse({
      technicalScore: 5,
      communicationScore: 5,
      starFrameworkCheck: true,
      constructiveCritique: '',
    });
    expect(result.success).toBe(false);
  });
});
