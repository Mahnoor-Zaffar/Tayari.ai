'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

type Difficulty = 'Junior' | 'Mid' | 'Senior' | 'Staff';
type Language = 'en' | 'ur';

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'Junior', label: 'Junior' },
  { value: 'Mid', label: 'Mid-Level' },
  { value: 'Senior', label: 'Senior' },
  { value: 'Staff', label: 'Staff' },
];

const LANGUAGES: { value: Language; label: string; desc: string }[] = [
  { value: 'en', label: 'English', desc: 'Full English interview' },
  { value: 'ur', label: 'Urdu (Hybrid)', desc: 'Mix of Urdu & English' },
];

export function NewInterviewForm() {
  const [targetRole, setTargetRole] = useState('');
  const [difficulty, setDifficulty] = useState<Difficulty>('Mid');
  const [language, setLanguage] = useState<Language>('en');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!targetRole.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/sessions/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetRole: targetRole.trim(), difficulty, language }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.error ?? 'Failed to create session');
      }

      const { sessionId } = await res.json();
      router.push(`/interview/${sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="role" className="block text-sm font-medium text-zinc-400">
          Target Role
        </label>
        <input
          id="role"
          type="text"
          value={targetRole}
          onChange={(e) => setTargetRole(e.target.value)}
          placeholder="e.g. Senior Frontend Engineer"
          className="mt-1.5 block w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 transition focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
          disabled={loading}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-400">
          Difficulty
        </label>
        <div className="mt-1.5 grid grid-cols-4 gap-2">
          {DIFFICULTIES.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => setDifficulty(value)}
              disabled={loading}
              className={`
                rounded-lg border px-3 py-2 text-sm font-medium transition
                ${difficulty === value
                  ? 'border-emerald-600 bg-emerald-950/20 text-emerald-400'
                  : 'border-zinc-700 bg-zinc-900 text-zinc-400 hover:border-zinc-500'
                }
                ${loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
              `}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-400">
          Interview Language
        </label>
        <div className="mt-1.5 grid grid-cols-2 gap-2">
          {LANGUAGES.map(({ value, label, desc }) => (
            <button
              key={value}
              type="button"
              onClick={() => setLanguage(value)}
              disabled={loading}
              className={`
                rounded-lg border px-3 py-2.5 text-left text-sm transition
                ${language === value
                  ? 'border-emerald-600 bg-emerald-950/20 text-emerald-400'
                  : 'border-zinc-700 bg-zinc-900 text-zinc-400 hover:border-zinc-500'
                }
                ${loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
              `}
            >
              <div className="font-medium">{label}</div>
              <div className="mt-0.5 text-xs opacity-70">{desc}</div>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading || !targetRole.trim()}
        className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? 'Creating...' : 'Start Interview'}
      </button>
    </form>
  );
}
