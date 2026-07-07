'use client';

import Link from 'next/link';

export interface SessionSummary {
  id: string;
  targetRole: string;
  difficulty: string;
  currentStage: string;
  isCompleted: boolean;
  createdAt: string;
}

interface SessionListProps {
  sessions: SessionSummary[];
}

const STAGE_LABELS: Record<string, string> = {
  INTRO: 'Intro',
  TECHNICAL: 'Technical',
  BEHAVIORAL: 'Behavioral',
  WRAP_UP: 'Wrap-up',
};

export function SessionList({ sessions }: SessionListProps) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <svg className="h-12 w-12 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
        <p className="text-sm text-zinc-600">No practice sessions yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sessions.map((session) => (
        <Link
          key={session.id}
          href={`/interview/${session.id}/report`}
          className="block rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 transition hover:border-zinc-700 hover:bg-zinc-900"
        >
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-sm font-semibold text-zinc-100">
                {session.targetRole}
              </h3>
              <p className="mt-0.5 text-xs text-zinc-500">
                {session.difficulty} &middot;{' '}
                {STAGE_LABELS[session.currentStage] ?? session.currentStage}
                {session.isCompleted ? ' &middot; Completed' : ' &middot; In Progress'}
              </p>
            </div>
            <div className="ml-4 flex items-center gap-3">
              <span className="whitespace-nowrap text-xs text-zinc-600">
                {new Date(session.createdAt).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                })}
              </span>
              <span
                className={`h-2 w-2 rounded-full ${
                  session.isCompleted ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
