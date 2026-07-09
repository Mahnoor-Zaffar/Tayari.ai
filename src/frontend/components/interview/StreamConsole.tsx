'use client';

import { useEffect, useRef } from 'react';
import { useInterviewStore } from '@/frontend/store/interview-store';

export function StreamConsole() {
  const { turns, transcript, streamedResponse, phase, error } =
    useInterviewStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);

  const isStreaming = phase === 'STREAMING_RESPONSE';
  const hasCurrentTurn = transcript || streamedResponse || isStreaming;

  /** Only auto-scroll if the user hasn't scrolled up. */
  useEffect(() => {
    if (isNearBottomRef.current) {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [streamedResponse, transcript, turns.length]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const threshold = 100;
    isNearBottomRef.current =
      el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden bg-zinc-950">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-6 py-3">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        <span className="text-xs uppercase tracking-wider text-zinc-500">
          Session Terminal
        </span>
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-6 font-mono text-sm leading-relaxed"
      >
        {error && (
          <div className="mb-4 rounded border border-red-900 bg-red-950/50 p-3 text-red-400">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* ---------- Completed turn history ---------- */}
          {turns.map((msg, i) => (
            <div key={i}>
              <div
                className={`mb-1 text-xs font-semibold uppercase tracking-wide ${
                  msg.type === 'user' ? 'text-zinc-500' : 'text-emerald-400'
                }`}
              >
                {msg.type === 'user' ? 'You' : 'AI Interviewer'}
              </div>
              <div
                className={`rounded-lg border p-3 ${
                  msg.type === 'user'
                    ? 'border-zinc-800 bg-zinc-900/50 text-zinc-300'
                    : 'border-zinc-800 bg-zinc-900/50 text-zinc-100'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {/* ---------- Current in-progress turn ---------- */}
          {transcript && (
            <div>
              <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                You
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-zinc-300">
                {transcript}
              </div>
            </div>
          )}

          {(streamedResponse || isStreaming) && (
            <div>
              <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-400">
                AI Interviewer
              </div>
              <div className="whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-zinc-100">
                {streamedResponse}
                {isStreaming && (
                  <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-emerald-400 align-text-bottom" />
                )}
              </div>
            </div>
          )}

          {!hasCurrentTurn && turns.length === 0 && phase === 'IDLE' && (
            <div className="py-12 text-center text-zinc-600">
              <p className="text-lg">Press the microphone to start</p>
              <p className="mt-1 text-sm">
                Your transcript and the AI response will appear here
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
