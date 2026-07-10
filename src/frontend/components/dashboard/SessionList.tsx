'use client';

import { useState, useRef } from 'react';
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

export function SessionList({ sessions: initialSessions }: SessionListProps) {
  const [sessions, setSessions] = useState(initialSessions);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (deleting) return;
    setDeleting(id);

    try {
      const res = await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.error ?? 'Delete failed');
      }
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      console.error('Failed to delete session:', err);
    } finally {
      setDeleting(null);
    }
  }

  function startEdit(id: string, currentRole: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setEditingId(id);
    setEditValue(currentRole);
    setTimeout(() => inputRef.current?.focus(), 10);
  }

  async function saveEdit(id: string) {
    if (!editValue.trim()) return;
    setEditingId(null);
    try {
      const res = await fetch(`/api/sessions/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetRole: editValue.trim() }),
      });
      if (!res.ok) return;
      setSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, targetRole: editValue.trim() } : s)),
      );
    } catch {
      // silently fail
    }
  }

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
        <div
          key={session.id}
          className="group relative rounded-lg border border-zinc-800 bg-zinc-900/50 transition hover:border-zinc-700 hover:bg-zinc-900"
        >
          <Link
            href={`/interview/${session.id}/report`}
            className="block p-4"
          >
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                {editingId === session.id ? (
                  <input
                    ref={inputRef}
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveEdit(session.id);
                      if (e.key === 'Escape') setEditingId(null);
                    }}
                    onBlur={() => saveEdit(session.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-full rounded border border-zinc-600 bg-zinc-800 px-2 py-0.5 text-sm font-semibold text-zinc-100 outline-none focus:border-emerald-600"
                  />
                ) : (
                  <div className="flex items-center gap-2">
                    <h3 className="truncate text-sm font-semibold text-zinc-100">
                      {session.targetRole}
                    </h3>
                    <button
                      onClick={(e) => startEdit(session.id, session.targetRole, e)}
                      className="shrink-0 rounded p-0.5 text-zinc-600 opacity-0 transition hover:text-zinc-400 group-hover:opacity-100"
                      aria-label="Rename session"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-3.5 w-3.5">
                        <path d="M21.731 2.269a2.625 2.625 0 0 0-3.712 0l-1.157 1.157 3.712 3.712 1.157-1.157a2.625 2.625 0 0 0 0-3.712ZM19.513 8.199l-3.712-3.712-8.4 8.4a5.25 5.25 0 0 0-1.32 2.214l-.8 2.685a.75.75 0 0 0 .933.933l2.685-.8a5.25 5.25 0 0 0 2.214-1.32l8.4-8.4Z" />
                        <path d="M5.25 5.25a3 3 0 0 0-3 3v10.5a3 3 0 0 0 3 3h10.5a3 3 0 0 0 3-3V13.5a.75.75 0 0 0-1.5 0v5.25a1.5 1.5 0 0 1-1.5 1.5H5.25a1.5 1.5 0 0 1-1.5-1.5V8.25a1.5 1.5 0 0 1 1.5-1.5h5.25a.75.75 0 0 0 0-1.5H5.25Z" />
                      </svg>
                    </button>
                  </div>
                )}
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

          <div className="flex items-center gap-2 border-t border-zinc-800 px-4 py-2">
            {!session.isCompleted && (
              <Link
                href={`/interview/${session.id}`}
                className="rounded bg-amber-600/20 px-2.5 py-1 text-xs font-medium text-amber-400 transition hover:bg-amber-600/30"
              >
                Continue
              </Link>
            )}
            <Link
              href={`/interview/${session.id}/report`}
              className="rounded bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-400 transition hover:bg-zinc-700"
            >
              Report
            </Link>
            <div className="flex-1" />
            <button
              onClick={(e) => handleDelete(session.id, e)}
              disabled={deleting === session.id}
              className="flex h-6 w-6 items-center justify-center rounded text-zinc-600 transition hover:bg-red-900/50 hover:text-red-400 disabled:opacity-30"
              aria-label="Delete session"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
                <path fillRule="evenodd" d="M16.5 4.478v.227a48.816 48.816 0 0 1 3.878.512.75.75 0 1 1-.256 1.478l-.209-.035-1.005 13.07a3 3 0 0 1-2.991 2.77H8.084a3 3 0 0 1-2.991-2.77L4.087 6.66l-.209.035a.75.75 0 0 1-.256-1.478A48.567 48.567 0 0 1 7.5 4.705v-.227c0-1.564 1.213-2.9 2.816-2.951a52.662 52.662 0 0 1 3.369 0c1.603.051 2.815 1.387 2.815 2.951Zm-6.136-1.452a51.196 51.196 0 0 1 3.273 0C14.39 3.05 15 3.684 15 4.478v.113a49.488 49.488 0 0 0-6 0v-.113c0-.794.609-1.428 1.364-1.452Zm-.355 5.945a.75.75 0 1 0-1.5.058l.347 9a.75.75 0 1 0 1.499-.058l-.346-9Zm5.48.058a.75.75 0 1 0-1.498-.058l-.347 9a.75.75 0 0 0 1.5.058l.345-9Z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
