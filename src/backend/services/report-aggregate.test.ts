import { describe, it, expect } from 'vitest';
import { computeAggregate } from './report-aggregate';
import type { TurnWithEvaluation } from './report-aggregate';

function makeTurn(overrides: Partial<TurnWithEvaluation['evaluation']> = {}): TurnWithEvaluation {
  return {
    id: '1',
    sequenceNumber: 1,
    interviewerQuestion: 'q?',
    candidateResponse: 'a.',
    evaluation: {
      technicalScore: 7,
      communicationScore: 8,
      starFrameworkCheck: true,
      concisenessScore: 4,
      confidenceScore: 4,
      codeQualityScore: 3,
      constructiveCritique: 'good',
      fillerWordsDetected: { um: 2, like: 1 },
      ...overrides,
    },
  };
}

describe('computeAggregate', () => {
  it('returns null scores for empty turns', () => {
    const result = computeAggregate([]);
    expect(result).toEqual({
      avgTechnical: null,
      avgCommunication: null,
      starRate: null,
      avgConciseness: null,
      avgConfidence: null,
      avgCodeQuality: null,
      totalTurns: 0,
      totalFillerWords: 0,
    });
  });

  it('skips turns without evaluation', () => {
    const turns: TurnWithEvaluation[] = [
      makeTurn(),
      { ...makeTurn(), id: '2', evaluation: null },
    ];
    const result = computeAggregate(turns);
    expect(result.totalTurns).toBe(2);
    expect(result.avgTechnical).toBe(7);
    expect(result.totalFillerWords).toBe(3);
  });

  it('computes averages correctly', () => {
    const turns = [
      makeTurn({ technicalScore: 6, communicationScore: 7 }),
      makeTurn({ technicalScore: 8, communicationScore: 9 }),
    ];
    const result = computeAggregate(turns);
    expect(result.avgTechnical).toBe(7);
    expect(result.avgCommunication).toBe(8);
  });

  it('computes star rate as percentage', () => {
    const turns = [
      makeTurn({ starFrameworkCheck: true }),
      makeTurn({ starFrameworkCheck: false }),
      makeTurn({ starFrameworkCheck: true }),
      makeTurn({ starFrameworkCheck: false }),
    ];
    const result = computeAggregate(turns);
    expect(result.starRate).toBe(50);
  });

  it('star rate is 100 when all pass', () => {
    const turns = [makeTurn({ starFrameworkCheck: true }), makeTurn({ starFrameworkCheck: true })];
    const result = computeAggregate(turns);
    expect(result.starRate).toBe(100);
  });

  it('star rate is 0 when none pass', () => {
    const turns = [makeTurn({ starFrameworkCheck: false }), makeTurn({ starFrameworkCheck: false })];
    const result = computeAggregate(turns);
    expect(result.starRate).toBe(0);
  });

  it('sums filler words across turns', () => {
    const turns = [
      makeTurn({ fillerWordsDetected: { um: 3, like: 2 } }),
      makeTurn({ fillerWordsDetected: { um: 1, yaani: 4 } }),
    ];
    const result = computeAggregate(turns);
    expect(result.totalFillerWords).toBe(10);
  });

  it('handles null scores gracefully', () => {
    const turns = [
      makeTurn({ technicalScore: null, communicationScore: null }),
      makeTurn({ technicalScore: 8, communicationScore: 9 }),
    ];
    const result = computeAggregate(turns);
    expect(result.avgTechnical).toBe(4);
    expect(result.avgCommunication).toBe(4.5);
  });

  it('computes all optional score fields', () => {
    const turns = [
      makeTurn({ concisenessScore: 3, confidenceScore: 4, codeQualityScore: 5 }),
    ];
    const result = computeAggregate(turns);
    expect(result.avgConciseness).toBe(3);
    expect(result.avgConfidence).toBe(4);
    expect(result.avgCodeQuality).toBe(5);
  });

  it('rounds averages to one decimal place', () => {
    const turns = [
      makeTurn({ technicalScore: 7 }),
      makeTurn({ technicalScore: 8 }),
      makeTurn({ technicalScore: 6 }),
    ];
    const result = computeAggregate(turns);
    expect(result.avgTechnical).toBe(7);
  });
});
