'use client';

import { useInterviewStore } from '@/frontend/store/interview-store';
import { WaveformVisualizer } from './WaveformVisualizer';

interface MicButtonProps {
  onToggle: () => void;
  onSkip: () => void;
  onEnd: () => void;
  isRecording: boolean;
  stream?: MediaStream | null;
}

const STATE_CONFIG: Record<string, { bg: string; ring: string; label: string; iconColor: string }> = {
  IDLE: {
    bg: 'bg-zinc-800 hover:bg-zinc-700',
    ring: 'ring-zinc-700',
    label: 'Start Interview',
    iconColor: 'text-zinc-300',
  },
  LISTENING: {
    bg: 'bg-red-600 hover:bg-red-700',
    ring: 'ring-red-500/50',
    label: 'Listening\u2026',
    iconColor: 'text-white',
  },
  PROCESSING: {
    bg: 'bg-amber-600',
    ring: 'ring-amber-500/30',
    label: 'Processing...',
    iconColor: 'text-white',
  },
  STREAMING_RESPONSE: {
    bg: 'bg-emerald-700',
    ring: 'ring-emerald-500/30',
    label: 'AI Responding',
    iconColor: 'text-white',
  },
} as const;

export function MicButton({ onToggle, onSkip, onEnd, stream }: MicButtonProps) {
  const { phase } = useInterviewStore();
  const cfg = STATE_CONFIG[phase];

  const isDisabled = phase === 'PROCESSING' || phase === 'STREAMING_RESPONSE';

  return (
    <div className="flex flex-col items-center gap-3">
      {phase === 'LISTENING' && (
        <WaveformVisualizer stream={stream ?? null} />
      )}

      <div className="flex items-center gap-4">
        {phase === 'LISTENING' && (
          <>
            <button
              onClick={onSkip}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-700 text-xs font-medium text-zinc-300 transition hover:bg-zinc-600 active:scale-95"
              aria-label="Skip question"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
                <path d="M5.055 7.06c-1.25-.714-2.805.189-2.805 1.628v4.383c0 1.439 1.555 2.342 2.805 1.628L12 10.398V15a1 1 0 0 0 1.555.832l6.75-4.5a1 1 0 0 0 0-1.664l-6.75-4.5A1 1 0 0 0 12 5.602v4.602L5.055 7.06Z" />
              </svg>
            </button>

            <button
              onClick={onEnd}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-700 text-xs font-medium text-zinc-300 transition hover:bg-red-800 hover:text-red-200 active:scale-95"
              aria-label="End interview"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
                <path d="M6.25 3A2.25 2.25 0 0 0 4 5.25v14.5A2.25 2.25 0 0 0 6.25 22h11.5A2.25 2.25 0 0 0 20 19.75V5.25A2.25 2.25 0 0 0 17.75 3H6.25ZM8 7.75a.75.75 0 0 1 .75-.75h6.5a.75.75 0 0 1 0 1.5h-6.5A.75.75 0 0 1 8 7.75Zm0 4a.75.75 0 0 1 .75-.75h6.5a.75.75 0 0 1 0 1.5h-6.5A.75.75 0 0 1 8 11.75Z" />
              </svg>
            </button>
          </>
        )}

        <button
          onClick={onToggle}
          disabled={isDisabled}
          className={`
            flex h-16 w-16 items-center justify-center
            rounded-full
            transition-all duration-200
            focus:outline-none focus:ring-2
            ring-offset-2 ring-offset-zinc-950
            ${cfg.bg} ${cfg.ring}
            ${isDisabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}
            ${phase === 'LISTENING' ? 'animate-pulse shadow-lg shadow-red-600/25' : ''}
            ${phase === 'IDLE' ? 'active:scale-95' : ''}
          `}
          aria-label={cfg.label}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={`h-7 w-7 ${cfg.iconColor}`}
          >
            <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10a1 1 0 0 0-2 0 5 5 0 0 1-10 0 1 1 0 0 0-2 0 7 7 0 0 0 6 6.93V20H8a1 1 0 1 0 0 2h8a1 1 0 1 0 0-2h-3v-3.07A7 7 0 0 0 19 10Z" />
          </svg>
        </button>
      </div>

      <span className="text-xs font-medium text-zinc-400">{cfg.label}</span>
    </div>
  );
}
