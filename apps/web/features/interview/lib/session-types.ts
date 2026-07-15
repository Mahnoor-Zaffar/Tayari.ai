/** WebSocket message types for the interview session protocol. */

export interface WSMessage {
  type: string;
  payload: Record<string, unknown>;
}

// ── Server → Client ──────────────────────────────────────────────────────────

export interface SessionConnectedPayload {
  session_id: string;
  state: string;
  remaining_seconds?: number;
}

export interface AIQuestionPayload {
  id: number;
  text: string;
  type: "initial" | "follow_up" | "wrap_up";
}

export interface AIHintPayload {
  text: string;
}

export interface TimerTickPayload {
  remaining_seconds: number;
  elapsed_seconds: number;
  state: string;
}

export interface TimerWarningPayload {
  remaining_seconds: number;
}

export interface SessionPausedPayload {
  session_id?: string;
  state?: string;
  remaining_seconds?: number;
}

export interface SessionResumedPayload {
  session_id?: string;
  state?: string;
  remaining_seconds?: number;
}

export interface SessionCompletedPayload {
  interview_id?: string;
  redirect_url?: string;
}

export interface ErrorPayload {
  code: string;
  message: string;
}

export type ServerEvent =
  | { type: "session.connected"; payload: SessionConnectedPayload }
  | { type: "ai.question"; payload: AIQuestionPayload }
  | { type: "ai.hint"; payload: AIHintPayload }
  | { type: "session.paused"; payload: SessionPausedPayload }
  | { type: "session.resumed"; payload: SessionResumedPayload }
  | { type: "session.completing"; payload: Record<string, unknown> }
  | { type: "session.completed"; payload: SessionCompletedPayload }
  | { type: "timer.tick"; payload: TimerTickPayload }
  | { type: "timer.warning"; payload: TimerWarningPayload }
  | { type: "heartbeat_ack"; payload: { timestamp: number } }
  | { type: "error"; payload: ErrorPayload };

// ── Interview Session State ──────────────────────────────────────────────────

export type SessionState =
  | "pending"
  | "initializing"
  | "active"
  | "paused"
  | "completing"
  | "completed"
  | "failed"
  | "timeout";

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "reconnecting";

export interface Question {
  id: number;
  text: string;
  type: "initial" | "follow_up" | "wrap_up";
  timestamp: number;
}

export interface TranscriptEntry {
  speaker: "ai" | "user";
  text: string;
  timestamp: number;
  is_final: boolean;
}

export interface InterviewSessionState {
  sessionId: string;
  interviewId: string;
  state: SessionState;
  questions: Question[];
  currentQuestion: Question | null;
  transcript: TranscriptEntry[];
  remainingSeconds: number;
  elapsedSeconds: number;
  connectionStatus: ConnectionStatus;
  isAiThinking: boolean;
  error: string | null;
}

export const DEFAULT_SESSION_STATE: InterviewSessionState = {
  sessionId: "",
  interviewId: "",
  state: "pending",
  questions: [],
  currentQuestion: null,
  transcript: [],
  remainingSeconds: 0,
  elapsedSeconds: 0,
  connectionStatus: "connecting",
  isAiThinking: false,
  error: null,
};
