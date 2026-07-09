'use client';

import { create } from 'zustand';
import type { TurnPhase } from '@/types/interview';

export interface ChatMessage {
  type: 'user' | 'assistant';
  text: string;
}

interface InterviewState {
  phase: TurnPhase;
  sessionId: string | null;
  transcript: string | null;
  streamedResponse: string;
  turnCount: number;
  error: string | null;
  /** Accumulated chat history — each completed turn pushed here. */
  turns: ChatMessage[];

  setSessionId: (id: string) => void;
  setPhase: (phase: TurnPhase) => void;
  setTranscript: (text: string) => void;
  appendChunk: (text: string) => void;
  pushTurn: (userText: string, assistantText: string) => void;
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
  turns: [],

  setSessionId: (id) => set({ sessionId: id }),
  setPhase: (phase) => set({ phase }),
  setTranscript: (text) => set({ transcript: text }),
  appendChunk: (text) =>
    set((state) => ({ streamedResponse: state.streamedResponse + text })),
  pushTurn: (userText, assistantText) =>
    set((state) => ({
      turns: [
        ...state.turns,
        { type: 'user', text: userText },
        { type: 'assistant', text: assistantText },
      ],
    })),
  incrementTurnCount: () =>
    set((state) => ({ turnCount: state.turnCount + 1 })),
  resetToIdle: () =>
    set({
      phase: 'LISTENING',
      transcript: null,
      streamedResponse: '',
      error: null,
    }),
  setError: (message) => set({ error: message, phase: 'LISTENING' }),
  clearError: () => set({ error: null }),
}));
