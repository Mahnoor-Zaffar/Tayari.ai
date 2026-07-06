'use client';

import { useInterviewStore } from '@/frontend/store/interview-store';
import { WaveformVisualizer } from './WaveformVisualizer';

interface MicButtonProps {
  onToggle: () => void;
  isRecording: boolean;
  stream?: MediaStream | null;
}

const STATE_CONFIG = {
  IDLE: {
    bg: 'bg-zinc-800 hover:bg-zinc-700',
    ring: 'ring-zinc-700',
    label: 'Start Speaking',
    iconColor: 'text-zinc-300',
  },
  RECORDING: {
    bg: 'bg-red-600 hover:bg-red-700',
    ring: 'ring-red-500/50',
    label: 'Tap to Stop',
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

export function MicButton({ onToggle, stream }: MicButtonProps) {
  const { phase } = useInterviewStore();
  const cfg = STATE_CONFIG[phase];

  const isDisabled = phase === 'PROCESSING' || phase === 'STREAMING_RESPONSE';

  return (
    <div className="flex flex-col items-center gap-3">
      {phase === 'RECORDING' && (
        <WaveformVisualizer stream={stream ?? null} />
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
          ${phase === 'RECORDING' ? 'animate-pulse shadow-lg shadow-red-600/25' : ''}
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

      <span className="text-xs font-medium text-zinc-400">{cfg.label}</span>
    </div>
  );
}
