"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import type {
  InterviewSessionState,
  ServerEvent,
  Question,
  TranscriptEntry,
  SessionState,
} from "@/features/interview/lib/session-types";
import { DEFAULT_SESSION_STATE } from "@/features/interview/lib/session-types";
import { SessionClient } from "@/features/interview/lib/session-client";
import { useInterviewTimer } from "./use-interview-timer";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const WS_BASE = API_BASE.replace(/^http/, "ws");

interface UseInterviewSessionOptions {
  sessionId: string;
  interviewId: string;
  token: string;
  durationMinutes?: number;
  onComplete?: (sessionId: string) => void;
}

export function useInterviewSession(options: UseInterviewSessionOptions) {
  const { sessionId, interviewId, token, durationMinutes = 30, onComplete } = options;
  const [state, setState] = useState<InterviewSessionState>({
    ...DEFAULT_SESSION_STATE,
    sessionId,
    interviewId,
    remainingSeconds: durationMinutes * 60,
  });
  const clientRef = useRef<SessionClient | null>(null);
  const stateRef = useRef(state);
  stateRef.current = state;

  const timer = useInterviewTimer(durationMinutes * 60);

  const updateState = useCallback((patch: Partial<InterviewSessionState>) => {
    setState((prev) => ({ ...prev, ...patch }));
  }, []);

  // ── Connect WebSocket ──────────────────────────────────────────────
  useEffect(() => {
    const wsUrl = `${WS_BASE}/sessions/${sessionId}/ws`;
    const client = new SessionClient(wsUrl, token);
    clientRef.current = client;

    client.subscribe((event) => {
      switch (event.type) {
        case "open":
          updateState({ connectionStatus: "connected" });
          break;

        case "close":
          if (event.code !== 1000) {
            updateState({ connectionStatus: "disconnected" });
          }
          break;

        case "message": {
          const serverEvent = event.data as ServerEvent;
          handleServerEvent(serverEvent);
          break;
        }

        case "error":
          if (event.error === "reconnecting") {
            updateState({ connectionStatus: "reconnecting" });
          } else if (event.error) {
            updateState({ error: event.error, connectionStatus: "disconnected" });
          }
          break;
      }
    });

    client.connect();

    return () => {
      client.close();
      clientRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, token]);

  // ── Handle server events ─────────────────────────────────────────
  const handleServerEvent = useCallback(
    (event: ServerEvent) => {
      switch (event.type) {
        case "session.connected": {
          const remaining = event.payload.remaining_seconds;
          if (remaining) {
            timer.reset(remaining);
          }
          break;
        }

        case "ai.question": {
          const q: Question = {
            id: event.payload.id,
            text: event.payload.text,
            type: event.payload.type,
            timestamp: Date.now(),
          };
          setState((prev) => ({
            ...prev,
            currentQuestion: q,
            questions: [...prev.questions, q],
            isAiThinking: false,
            transcript: [
              ...prev.transcript,
              { speaker: "ai", text: event.payload.text, timestamp: Date.now(), is_final: true },
            ],
          }));
          break;
        }

        case "ai.hint": {
          setState((prev) => ({
            ...prev,
            isAiThinking: false,
            transcript: [
              ...prev.transcript,
              { speaker: "ai", text: event.payload.text, timestamp: Date.now(), is_final: true },
            ],
          }));
          break;
        }

        case "session.paused":
          timer.pause();
          updateState({ state: "paused" });
          if (event.payload.remaining_seconds != null) {
            timer.sync(event.payload.remaining_seconds, 0);
          }
          break;

        case "session.resumed":
          timer.resume();
          updateState({ state: "active" });
          if (event.payload.remaining_seconds != null) {
            timer.sync(event.payload.remaining_seconds, 0);
          }
          break;

        case "session.completing":
          updateState({ state: "completing" });
          break;

        case "session.completed":
          timer.pause();
          updateState({ state: "completed" });
          onComplete?.(sessionId);
          break;

        case "timer.tick":
          timer.sync(event.payload.remaining_seconds, event.payload.elapsed_seconds);
          break;

        case "timer.warning":
          // Flash/timer warning handled by UI component
          break;

        case "error":
          updateState({ error: event.payload.message });
          break;
      }
    },
    [timer, updateState, sessionId, onComplete],
  );

  // ── Actions ────────────────────────────────────────────────────────
  const sendAnswer = useCallback((text: string) => {
    clientRef.current?.send("user.answer", { text, timestamp_ms: Date.now() });
    setState((prev) => ({
      ...prev,
      isAiThinking: true,
      transcript: [
        ...prev.transcript,
        { speaker: "user", text, timestamp: Date.now(), is_final: true },
      ],
    }));
  }, []);

  const pauseSession = useCallback(() => {
    clientRef.current?.send("session.pause");
  }, []);

  const resumeSession = useCallback(() => {
    clientRef.current?.send("session.resume");
  }, []);

  const requestHint = useCallback(() => {
    updateState({ isAiThinking: true });
    clientRef.current?.send("session.request_hint");
  }, [updateState]);

  const endSession = useCallback(() => {
    clientRef.current?.send("session.end");
    timer.pause();
    updateState({ state: "completed" });
  }, [timer, updateState]);

  const reconnect = useCallback(() => {
    clientRef.current?.connect();
  }, []);

  return {
    state,
    timer,
    sendAnswer,
    pauseSession,
    resumeSession,
    requestHint,
    endSession,
    reconnect,
  };
}
