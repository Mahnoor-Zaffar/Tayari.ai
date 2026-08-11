"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ttsApi } from "@/features/interview/api/tts";
import type { Question } from "@/features/interview/lib/session-types";

interface UseQuestionTtsOptions {
  /** Access token used to authenticate the TTS requests. */
  token: string;
  /** The latest question — a new value triggers speech synthesis. */
  currentQuestion: Question | null;
  /**
   * Called when this question's playback finished (or was skipped after an
   * attempted fetch) so the caller can start the microphone.
   */
  onQuestionEnd?: () => void;
}

interface UseQuestionTtsResult {
  /** Whether real TTS is available (mock fallback is silent and skipped). */
  supported: boolean;
  /** True while synthesized audio is playing. */
  isPlaying: boolean;
  /** Stop current playback (barge-in) and ignore in-flight fetches. */
  stop: () => void;
}

/**
 * Speaks each new interview question via the server TTS bridge.
 *
 * - Fetches availability once on mount; when the backend only has the silent
 *   mock provider, playback is disabled and text/mic flow is unchanged.
 * - Dedupes by question timestamp so reconnects that replay the current
 *   question are re-spoken (desired) while re-renders are not.
 * - ``stop`` enables barge-in: the caller interrupts playback the moment the
 *   user starts talking.
 */
export function useQuestionTts({
  token,
  currentQuestion,
  onQuestionEnd,
}: UseQuestionTtsOptions): UseQuestionTtsResult {
  const [supported, setSupported] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);
  const playedTimestampRef = useRef(0);
  const inFlightRef = useRef(false);
  const onQuestionEndRef = useRef(onQuestionEnd);
  onQuestionEndRef.current = onQuestionEnd;

  const stop = useCallback(() => {
    inFlightRef.current = false;
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.src = "";
    }
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  // Stop playback and ignore in-flight work when the session unmounts.
  useEffect(() => {
    return () => {
      inFlightRef.current = false;
      const audio = audioRef.current;
      if (audio) audio.src = "";
      if (urlRef.current) {
        URL.revokeObjectURL(urlRef.current);
        urlRef.current = null;
      }
    };
  }, []);

  // Detect availability once so we never auto-play silent mock audio.
  useEffect(() => {
    let active = true;
    ttsApi
      .getStatus()
      .then((status) => {
        if (active) setSupported(status.available);
      })
      .catch(() => {
        if (active) setSupported(false);
      });
    return () => {
      active = false;
    };
  }, []);

  // Speak each new question.
  useEffect(() => {
    if (!currentQuestion || !supported) return;
    if (currentQuestion.timestamp === playedTimestampRef.current) return;
    playedTimestampRef.current = currentQuestion.timestamp;

    const finished = () => {
      if (!inFlightRef.current) return;
      inFlightRef.current = false;
      setIsPlaying(false);
      onQuestionEndRef.current?.();
    };

    inFlightRef.current = true;
    setIsPlaying(true);

    ttsApi
      .synthesizeToBlobUrl(token, currentQuestion.text)
      .then((url) => {
        if (!inFlightRef.current) {
          URL.revokeObjectURL(url);
          return;
        }
        if (urlRef.current) {
          URL.revokeObjectURL(urlRef.current);
        }
        const audio = audioRef.current ?? new Audio();
        audioRef.current = audio;
        urlRef.current = url;
        audio.onended = finished;
        audio.src = url;
        void audio.play().catch(finished);
      })
      .catch(finished);
  }, [currentQuestion, token, supported, stop]);

  return { supported, isPlaying, stop };
}
