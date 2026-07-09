// =============================================================================
// Tayari.ai — Domain Type Definitions
// Version: 1.0.0
// -----------------------------------------------------------------------------
// All interfaces map 1:1 to the underlying Supabase/PostgreSQL schema defined
// in database/001_initialize_schema.sql.  camelCase properties are serialized
// to snake_case at the API boundary (see serialisation helpers).
// =============================================================================

// ---------------------------------------------------------------------------
// Enums / Union Litterals
// ---------------------------------------------------------------------------

export type InterviewStage = 'INTRO' | 'TECHNICAL' | 'BEHAVIORAL' | 'WRAP_UP';

export type Difficulty = 'Junior' | 'Mid' | 'Senior' | 'Staff';

export type TurnPhase = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'STREAMING_RESPONSE' | 'COMPLETE';

// ---------------------------------------------------------------------------
// Interview lifecycle constants
// ---------------------------------------------------------------------------

export const MAX_TURNS = 8;

/** Turn-number ranges for each stage (1-indexed). */
export const STAGE_TURN_RANGES: Record<InterviewStage, [number, number]> = {
  INTRO: [1, 2],
  TECHNICAL: [3, 5],
  BEHAVIORAL: [6, 8],
  WRAP_UP: [9, 9],
};

// ---------------------------------------------------------------------------
// Core Domain Entities
// ---------------------------------------------------------------------------

export interface InterviewSession {
  id: string;
  userId: string;
  targetRole: string;
  difficulty: Difficulty;
  currentStage: InterviewStage;
  resumeContext: string | null;
  isCompleted: boolean;
  createdAt: string;
}

export interface InterviewTurn {
  id: string;
  sessionId: string;
  sequenceNumber: number;
  interviewerQuestion: string;
  candidateResponse: string;
  createdAt: string;
}

export interface TurnEvaluation {
  id: string;
  turnId: string;
  technicalScore: number | null;
  communicationScore: number | null;
  starFrameworkCheck: boolean;
  concisenessScore: number | null;
  confidenceScore: number | null;
  codeQualityScore: number | null;
  constructiveCritique: string | null;
  fillerWordsDetected: Record<string, number>;
  createdAt: string;
}

export interface ResumeEmbedding {
  id: number;
  userId: string;
  content: string;
  embedding: number[];
  metadata: Record<string, unknown>;
  createdAt: string;
}

/** Determine which interview stage a turn number belongs to. */
export function stageForTurnNumber(turnNumber: number): InterviewStage {
  for (const [stage, [start, end]] of Object.entries(STAGE_TURN_RANGES)) {
    if (turnNumber >= start && turnNumber <= end) return stage as InterviewStage;
  }
  return 'WRAP_UP';
}

// ---------------------------------------------------------------------------
// API / Wire-Protocol Shapes
// ---------------------------------------------------------------------------

export interface TurnAudioPayload {
  audio: Blob;
  sessionId: string;
  userId: string;
}

export interface EvaluateTurnWebhookPayload {
  turnId: string;
  interviewerQuestion: string;
  candidateResponse: string;
}

// ---------------------------------------------------------------------------
// Shadow Evaluator — LLM JSON Contract
// ---------------------------------------------------------------------------

export interface ShadowEvaluatorContract {
  technicalScore: number;
  communicationScore: number;
  starFrameworkCheck: boolean;
  concisenessScore: number;
  confidenceScore: number;
  codeQualityScore: number;
  constructiveCritique: string;
}

// ---------------------------------------------------------------------------
// SSE Stream Events (server → client)
// ---------------------------------------------------------------------------

export interface TranscriptEvent {
  text: string;
}

export interface ChunkEvent {
  text: string;
}

export interface DoneEvent {
  turnId: string;
  interviewerQuestion: string;
  candidateResponse: string;
  completed?: boolean;
}

export type SSEEvent =
  | { type: 'TRANSCRIPT'; data: TranscriptEvent }
  | { type: 'CHUNK'; data: ChunkEvent }
  | { type: 'DONE'; data: DoneEvent }
  | { type: 'ERROR'; data: { message: string } };

// ---------------------------------------------------------------------------
// RAG / Vector-Search Result
// ---------------------------------------------------------------------------

export interface MatchedResumeChunk {
  id: number;
  userId: string;
  content: string;
  metadata: Record<string, unknown>;
  similarity: number;
}

// ---------------------------------------------------------------------------
// Session Creation Input (used when starting a new interview)
// ---------------------------------------------------------------------------

export interface CreateSessionInput {
  userId: string;
  targetRole: string;
  difficulty: Difficulty;
  resumeContext?: string;
}
