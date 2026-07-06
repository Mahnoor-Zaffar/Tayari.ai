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

export type TurnPhase = 'IDLE' | 'RECORDING' | 'PROCESSING' | 'STREAMING';

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

export type SSEEvent =
  | { type: 'TRANSCRIPT'; data: TranscriptEvent }
  | { type: 'CHUNK'; data: ChunkEvent }
  | { type: 'DONE'; data: null }
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
