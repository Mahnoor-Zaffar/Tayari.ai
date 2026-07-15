"use client";

import { useEffect, useRef, useCallback, useState } from "react";

interface TimerState {
  remaining: number;
  elapsed: number;
  isRunning: boolean;
  isPaused: boolean;
}

interface TimerControls {
  pause: () => void;
  resume: () => void;
  reset: (durationSeconds: number) => void;
  sync: (remaining: number, elapsed: number) => void;
}

export function useInterviewTimer(
  initialDurationSeconds = 1800,
): TimerState & TimerControls {
  const [state, setState] = useState<TimerState>({
    remaining: initialDurationSeconds,
    elapsed: 0,
    isRunning: false,
    isPaused: false,
  });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stateRef = useRef(state);
  stateRef.current = state;

  const clearTick = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startTick = useCallback(() => {
    clearTick();
    intervalRef.current = setInterval(() => {
      setState((prev) => {
        if (prev.remaining <= 0 || prev.isPaused) return prev;
        return {
          ...prev,
          remaining: prev.remaining - 1,
          elapsed: prev.elapsed + 1,
        };
      });
    }, 1000);
  }, [clearTick]);

  const pause = useCallback(() => {
    setState((prev) => ({ ...prev, isPaused: true }));
    clearTick();
  }, [clearTick]);

  const resume = useCallback(() => {
    setState((prev) => ({ ...prev, isPaused: false }));
    startTick();
  }, [startTick]);

  const reset = useCallback(
    (durationSeconds: number) => {
      clearTick();
      setState({
        remaining: durationSeconds,
        elapsed: 0,
        isRunning: true,
        isPaused: false,
      });
      startTick();
    },
    [clearTick, startTick],
  );

  const sync = useCallback((remaining: number, elapsed: number) => {
    setState((prev) => ({
      ...prev,
      remaining,
      elapsed,
    }));
  }, []);

  useEffect(() => {
    return clearTick;
  }, [clearTick]);

  return { ...state, pause, resume, reset, sync };
}
