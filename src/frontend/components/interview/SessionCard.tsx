'use client';

import { useInterviewStore } from '@/frontend/store/interview-store';

const PHASE_LABELS: Record<string, { color: string; text: string }> = {
  IDLE: { color: 'bg-zinc-500', text: 'Ready' },
  LISTENING: { color: 'bg-red-500', text: 'Listening' },
  PROCESSING: { color: 'bg-amber-500', text: 'Processing' },
  STREAMING_RESPONSE: { color: 'bg-emerald-500', text: 'Streaming' },
};

export function SessionCard() {
  const { sessionId, phase, turnCount } = useInterviewStore();
  const status = PHASE_LABELS[phase] ?? PHASE_LABELS.IDLE;

  return (
    <div className="flex w-72 shrink-0 flex-col gap-6 border-r border-zinc-800 bg-zinc-950 p-6">
      <div className="space-y-1">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
          Session
        </h2>
        <p className="truncate font-mono text-xs text-zinc-400">
          {sessionId ?? '\u2014'}
        </p>
      </div>

      <div className="space-y-3">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-500">Status</span>
            <span className={`h-2 w-2 rounded-full ${status.color}`} />
          </div>
          <div className="mt-1 font-semibold text-zinc-100">{status.text}</div>
        </div>

        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
          <div className="text-xs text-zinc-500">Turns Completed</div>
          <div className="mt-1 font-semibold text-zinc-100">{turnCount}</div>
        </div>

        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
          <div className="text-xs text-zinc-500">Phase</div>
          <div className="mt-1 font-mono text-xs text-zinc-400">{phase}</div>
        </div>
      </div>
    </div>
  );
}
