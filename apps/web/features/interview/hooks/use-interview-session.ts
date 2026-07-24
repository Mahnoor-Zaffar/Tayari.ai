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

  const timer = useInterviewTimer(durationMinutes * 60);

  const updateState = useCallback((patch: Partial<InterviewSessionState>) => {
    setState((prev) => ({ ...prev, ...patch }));
  }, []);

  // ── Handle server events ─────────────────────────────────────────
  // Defined as a ref so the WS subscribe callback always calls the latest version
  // without needing to re-subscribe when deps change.
  const handleServerEvent = useCallback(
    (event: ServerEvent) => {
      switch (event.type) {
        case "session.connected": {
          const remaining = event.payload.remaining_seconds;
          if (remaining) {
            timer.reset(remaining);
          }
          if (event.payload.state) {
            updateState({ state: event.payload.state as SessionState });
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

        case "ai.stream_start": {
          setState((prev) => ({
            ...prev,
            isAiThinking: false,
            transcript: [
              ...prev.transcript,
              { speaker: "ai", text: "", timestamp: Date.now(), is_final: false },
            ],
          }));
          break;
        }

        case "ai.token": {
          setState((prev) => {
            const updated = [...prev.transcript];
            const last = updated[updated.length - 1];
            if (last && last.speaker === "ai" && !last.is_final) {
              updated[updated.length - 1] = {
                ...last,
                text: last.text + event.payload.token,
              };
            }
            return { ...prev, transcript: updated };
          });
          break;
        }

        case "ai.stream_end": {
          setState((prev) => {
            const updated = [...prev.transcript];
            const last = updated[updated.length - 1];
            if (last && last.speaker === "ai") {
              updated[updated.length - 1] = { ...last, is_final: true };
            }
            const q: Question = {
              id: 0,
              text: event.payload.text,
              type: "follow_up",
              timestamp: Date.now(),
            };
            return {
              ...prev,
              currentQuestion: q,
              questions: [...prev.questions, q],
              transcript: updated,
            };
          });
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
          break;

        case "error":
          updateState({ error: event.payload.message });
          break;
      }
    },
    [timer, updateState, sessionId, onComplete],
  );

  // Keep a ref to the latest handler so the WS subscribe callback is never stale
  const handleServerEventRef = useRef(handleServerEvent);
  handleServerEventRef.current = handleServerEvent;

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

        case "message":
          handleServerEventRef.current(event.data as ServerEvent);
          break;

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
  }, []);

  const undoLastAnswer = useCallback(() => {
    setState((prev) => {
      if (!prev.isAiThinking) return prev;
      const lastUserIdx = [...prev.transcript].reverse().findIndex((e) => e.speaker === "user");
      if (lastUserIdx === -1) return prev;
      const actualIdx = prev.transcript.length - 1 - lastUserIdx;
      return {
        ...prev,
        transcript: prev.transcript.filter((_, i) => i !== actualIdx),
      };
    });
  }, []);

  const reconnect = useCallback(() => {
    const client = clientRef.current;
    if (client) {
      client.connect();
    }
  }, []);

  return {
    state,
    timer,
    sendAnswer,
    undoLastAnswer,
    pauseSession,
    resumeSession,
    requestHint,
    endSession,
    reconnect,
  };
}
