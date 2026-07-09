import { createClient } from '@supabase/supabase-js';
import type {
  InterviewSession,
  InterviewTurn,
  InterviewStage,
  MatchedResumeChunk,
  TurnEvaluation,
} from '@/types/interview';
import { mapRowToCamel, mapRowsToCamel } from '@/backend/services/utils';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
);

export async function fetchSession(sessionId: string): Promise<InterviewSession> {
  const { data, error } = await supabase
    .from('interview_sessions')
    .select('*')
    .eq('id', sessionId)
    .single();

  if (error || !data) {
    throw new Error(`Session not found: ${sessionId}`);
  }

  return mapRowToCamel<InterviewSession>(data as Record<string, unknown>);
}

export async function fetchTurnHistory(
  sessionId: string,
): Promise<InterviewTurn[]> {
  const { data, error } = await supabase
    .from('interview_turns')
    .select('*')
    .eq('session_id', sessionId)
    .order('sequence_number', { ascending: true });

  if (error) {
    throw new Error(`Failed to fetch turn history: ${error.message}`);
  }

  return mapRowsToCamel<InterviewTurn>((data ?? []) as Record<string, unknown>[]);
}

export async function searchResumeContext(
  embedding: number[],
  userId: string,
  matchThreshold = 0.7,
  matchCount = 5,
): Promise<MatchedResumeChunk[]> {
  const { data, error } = await supabase.rpc('match_resume_chunks', {
    query_embedding: embedding,
    query_user_id: userId,
    match_threshold: matchThreshold,
    match_count: matchCount,
  });

  if (error) {
    throw new Error(`RAG search failed: ${error.message}`);
  }

  return mapRowsToCamel<MatchedResumeChunk>((data ?? []) as Record<string, unknown>[]);
}

export async function insertTurn(params: {
  sessionId: string;
  sequenceNumber: number;
  interviewerQuestion: string;
  candidateResponse: string;
}): Promise<string> {
  const { data, error } = await supabase
    .from('interview_turns')
    .insert({
      session_id: params.sessionId,
      sequence_number: params.sequenceNumber,
      interviewer_question: params.interviewerQuestion,
      candidate_response: params.candidateResponse,
    })
    .select('id')
    .single();

  if (error) {
    throw new Error(`Failed to persist turn: ${error.message}`);
  }

  return data.id;
}

export async function updateSessionStage(
  sessionId: string,
  stage: InterviewStage,
): Promise<void> {
  const { error } = await supabase
    .from('interview_sessions')
    .update({ current_stage: stage })
    .eq('id', sessionId);

  if (error) {
    throw new Error(`Failed to update session stage: ${error.message}`);
  }
}

export async function upsertEvaluation(params: {
  turnId: string;
  technicalScore: number;
  communicationScore: number;
  starFrameworkCheck: boolean;
  concisenessScore: number;
  confidenceScore: number;
  codeQualityScore: number;
  constructiveCritique: string;
  fillerWordsDetected: Record<string, number>;
}): Promise<void> {
  const payload: Record<string, unknown> = {
    turn_id: params.turnId,
    technical_score: params.technicalScore,
    communication_score: params.communicationScore,
    star_framework_check: params.starFrameworkCheck,
    constructive_critique: params.constructiveCritique,
    filler_words_detected: params.fillerWordsDetected,
  };

  // New columns — may not exist in older databases; try and catch gracefully
  try {
    const { error } = await supabase.from('turn_evaluations').upsert(
      {
        ...payload,
        conciseness_score: params.concisenessScore,
        confidence_score: params.confidenceScore,
        code_quality_score: params.codeQualityScore,
      },
      { onConflict: 'turn_id' },
    );
    if (error) throw error;
  } catch {
    // Fallback: columns don't exist yet — try without them
    const { error } = await supabase.from('turn_evaluations').upsert(
      payload,
      { onConflict: 'turn_id' },
    );
    if (error) {
      throw new Error(`Failed to upsert evaluation: ${error.message}`);
    }
  }
}

export async function completeSession(
  sessionId: string,
  overallAssessment?: string,
): Promise<void> {
  const update: Record<string, unknown> = { is_completed: true };
  if (overallAssessment) update.overall_assessment = overallAssessment;

  const { error } = await supabase
    .from('interview_sessions')
    .update(update)
    .eq('id', sessionId);

  if (error) {
    throw new Error(`Failed to complete session: ${error.message}`);
  }
}

// ---------------------------------------------------------------------------
// Session Report (turns + evaluations joined)
// ---------------------------------------------------------------------------

export interface TurnWithEvaluation extends InterviewTurn {
  evaluation: TurnEvaluation | null;
}

export async function fetchSessionReport(
  sessionId: string,
): Promise<TurnWithEvaluation[]> {
  const { data, error } = await supabase
    .from('interview_turns')
    .select('*, turn_evaluations(*)')
    .eq('session_id', sessionId)
    .order('sequence_number', { ascending: true });

  if (error) {
    throw new Error(`Failed to fetch session report: ${error.message}`);
  }

  return ((data ?? []) as Record<string, unknown>[]).map((row) => {
    const { turn_evaluations, ...turn } = row;
    return {
      ...mapRowToCamel<InterviewTurn>(turn as Record<string, unknown>),
      evaluation: turn_evaluations
        ? mapRowToCamel<TurnEvaluation>(
            turn_evaluations as Record<string, unknown>,
          )
        : null,
    };
  });
}
