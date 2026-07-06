'use client';

import { create } from 'zustand';
import type { TurnPhase } from '@/types/interview';

interface InterviewState {
  phase: TurnPhase;
  sessionId: string | null;
  transcript: string | null;
  streamedResponse: string;
  turnCount: number;
  error: string | null;

  setSessionId: (id: string) => void;
  setPhase: (phase: TurnPhase) => void;
  setTranscript: (text: string) => void;
  appendChunk: (text: string) => void;
  incrementTurnCount: () => void;
  resetToIdle: () => void;
  setError: (message: string) => void;
  clearError: () => void;
}

export const useInterviewStore = create<InterviewState>((set) => ({
  phase: 'IDLE',
  sessionId: null,
  transcript: null,
  streamedResponse: '',
  turnCount: 0,
  error: null,

  setSessionId: (id) => set({ sessionId: id }),
  setPhase: (phase) => set({ phase }),
  setTranscript: (text) => set({ transcript: text }),
  appendChunk: (text) =>
    set((state) => ({ streamedResponse: state.streamedResponse + text })),
  incrementTurnCount: () =>
    set((state) => ({ turnCount: state.turnCount + 1 })),
  resetToIdle: () =>
    set({
      phase: 'IDLE',
      transcript: null,
      streamedResponse: '',
      error: null,
    }),
  setError: (message) => set({ error: message, phase: 'IDLE' }),
  clearError: () => set({ error: null }),
}));
