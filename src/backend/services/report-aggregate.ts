export interface TurnWithEvaluation {
  id: string;
  sequenceNumber: number;
  interviewerQuestion: string;
  candidateResponse: string;
  evaluation: {
    technicalScore: number | null;
    communicationScore: number | null;
    starFrameworkCheck: boolean;
    concisenessScore: number | null;
    confidenceScore: number | null;
    codeQualityScore: number | null;
    constructiveCritique: string | null;
    fillerWordsDetected: Record<string, number>;
  } | null;
}

export interface Aggregate {
  avgTechnical: number | null;
  avgCommunication: number | null;
  starRate: number | null;
  avgConciseness: number | null;
  avgConfidence: number | null;
  avgCodeQuality: number | null;
  totalTurns: number;
  totalFillerWords: number;
}

function avg(scores: (number | null)[], evaluatedCount: number): number | null {
  if (evaluatedCount === 0) return null;
  const sum = scores.reduce<number>((s, n) => s + (n ?? 0), 0);
  return Math.round((sum / evaluatedCount) * 10) / 10;
}

export function computeAggregate(turns: TurnWithEvaluation[]): Aggregate {
  const evaluated = turns.filter((t) => t.evaluation);

  const avgTechnical = avg(evaluated.map((t) => t.evaluation!.technicalScore), evaluated.length);
  const avgCommunication = avg(evaluated.map((t) => t.evaluation!.communicationScore), evaluated.length);
  const avgConciseness = avg(evaluated.map((t) => t.evaluation!.concisenessScore), evaluated.length);
  const avgConfidence = avg(evaluated.map((t) => t.evaluation!.confidenceScore), evaluated.length);
  const avgCodeQuality = avg(evaluated.map((t) => t.evaluation!.codeQualityScore), evaluated.length);

  const starCount = evaluated.filter((t) => t.evaluation!.starFrameworkCheck).length;
  const starRate = evaluated.length > 0 ? Math.round((starCount / evaluated.length) * 100) : null;

  const totalFillerWords = evaluated.reduce((s, t) => {
    const fw = t.evaluation!.fillerWordsDetected ?? {};
    return s + Object.values(fw).reduce((a, b) => a + b, 0);
  }, 0);

  return {
    avgTechnical,
    avgCommunication,
    starRate,
    avgConciseness,
    avgConfidence,
    avgCodeQuality,
    totalTurns: turns.length,
    totalFillerWords,
  };
}
