// =============================================================================
// Tayari.ai — Supabase / PostgreSQL Data Access Layer
// =============================================================================

import { createClient } from '@supabase/supabase-js';
import type {
  InterviewSession,
  InterviewTurn,
  InterviewStage,
  MatchedResumeChunk,
} from '@/types/interview';
import { mapRowToCamel, mapRowsToCamel } from '@/lib/utils';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
);

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Conversation History (chronological)
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Resume Vector Search (RAG)
// ---------------------------------------------------------------------------

export async function searchResumeContext(
  embedding: number[],
  matchThreshold = 0.7,
  matchCount = 5,
): Promise<MatchedResumeChunk[]> {
  const { data, error } = await supabase.rpc('match_resume_chunks', {
    query_embedding: `[${embedding.join(',')}]`,
    match_threshold: matchThreshold,
    match_count: matchCount,
  });

  if (error) {
    throw new Error(`RAG search failed: ${error.message}`);
  }

  return mapRowsToCamel<MatchedResumeChunk>((data ?? []) as Record<string, unknown>[]);
}

// ---------------------------------------------------------------------------
// Turn Persistence (insert on stream completion)
// ---------------------------------------------------------------------------

export async function insertTurn(params: {
  sessionId: string;
  sequenceNumber: number;
  interviewerQuestion: string;
  candidateResponse: string;
}): Promise<void> {
  const { error } = await supabase.from('interview_turns').insert({
    session_id: params.sessionId,
    sequence_number: params.sequenceNumber,
    interviewer_question: params.interviewerQuestion,
    candidate_response: params.candidateResponse,
  });

  if (error) {
    throw new Error(`Failed to persist turn: ${error.message}`);
  }
}

// ---------------------------------------------------------------------------
// Session Stage Progression
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Evaluation Upsert (background worker)
// ---------------------------------------------------------------------------

export async function upsertEvaluation(params: {
  turnId: string;
  technicalScore: number;
  communicationScore: number;
  starFrameworkCheck: boolean;
  constructiveCritique: string;
  fillerWordsDetected: Record<string, number>;
}): Promise<void> {
  const { error } = await supabase.from('turn_evaluations').upsert(
    {
      turn_id: params.turnId,
      technical_score: params.technicalScore,
      communication_score: params.communicationScore,
      star_framework_check: params.starFrameworkCheck,
      constructive_critique: params.constructiveCritique,
      filler_words_detected: params.fillerWordsDetected,
    },
    { onConflict: 'turn_id' },
  );

  if (error) {
    throw new Error(`Failed to upsert evaluation: ${error.message}`);
  }
}
