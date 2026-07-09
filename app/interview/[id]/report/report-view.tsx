'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { TurnWithEvaluation } from '@/backend/db/database';

interface Aggregate {
  avgTechnical: number | null;
  avgCommunication: number | null;
  starRate: number | null;
  avgConciseness: number | null;
  avgConfidence: number | null;
  avgCodeQuality: number | null;
  totalTurns: number;
  totalFillerWords: number;
}

export function ReportView({
  sessionId,
  turns,
  aggregate,
}: {
  sessionId: string;
  turns: TurnWithEvaluation[];
  aggregate: Aggregate;
}) {
  const [expandedTurn, setExpandedTurn] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-black text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <h1 className="text-lg font-semibold">Session Report</h1>
        <Link
          href={`/interview/${sessionId}`}
          className="rounded bg-zinc-800 px-3 py-1.5 text-sm text-zinc-300 transition hover:bg-zinc-700"
        >
          Back to Interview
        </Link>
      </header>

      <div className="mx-auto max-w-4xl space-y-8 p-6">
        {/* Scorecard Grid */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <ScoreCard
            label="Technical"
            value={
              aggregate.avgTechnical !== null
                ? `${aggregate.avgTechnical}/10`
                : '—'
            }
          />
          <ScoreCard
            label="Communication"
            value={
              aggregate.avgCommunication !== null
                ? `${aggregate.avgCommunication}/10`
                : '—'
            }
          />
          <ScoreCard
            label="Conciseness"
            value={
              aggregate.avgConciseness !== null
                ? `${aggregate.avgConciseness}/5`
                : '—'
            }
          />
          <ScoreCard
            label="Confidence"
            value={
              aggregate.avgConfidence !== null
                ? `${aggregate.avgConfidence}/5`
                : '—'
            }
          />
          <ScoreCard
            label="Code Quality"
            value={
              aggregate.avgCodeQuality !== null
                ? `${aggregate.avgCodeQuality}/5`
                : '—'
            }
          />
          <ScoreCard
            label="STAR Adherence"
            value={
              aggregate.starRate !== null ? `${aggregate.starRate}%` : '—'
            }
          />
          <ScoreCard
            label="Filler Words"
            value={String(aggregate.totalFillerWords)}
          />
        </div>

        {/* Turn-by-Turn Breakdown */}
        <section>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Transcript ({turns.length} turns)
          </h2>

          {turns.length === 0 && (
            <p className="py-8 text-center text-zinc-600">
              No turns recorded yet.
            </p>
          )}

          <div className="space-y-3">
            {turns.map((turn) => {
              const isOpen = expandedTurn === turn.id;
              const ev = turn.evaluation;

              return (
                <div
                  key={turn.id}
                  className="rounded-lg border border-zinc-800 bg-zinc-900/50"
                >
                  <button
                    onClick={() =>
                      setExpandedTurn(isOpen ? null : turn.id)
                    }
                    className="flex w-full items-center justify-between px-4 py-3 text-left transition hover:bg-zinc-800/50"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex h-6 w-6 items-center justify-center rounded bg-zinc-800 text-xs font-mono text-zinc-400">
                        {turn.sequenceNumber}
                      </span>
                      <span className="text-sm text-zinc-300 line-clamp-1">
                        {turn.interviewerQuestion.slice(0, 80)}
                        {turn.interviewerQuestion.length > 80 ? '...' : ''}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      {ev && (
                        <>
                          <span
                            className={`text-xs font-mono ${
                              (ev.technicalScore ?? 0) >= 7
                                ? 'text-emerald-400'
                                : (ev.technicalScore ?? 0) >= 4
                                  ? 'text-amber-400'
                                  : 'text-red-400'
                            }`}
                          >
                            T{ev.technicalScore}
                          </span>
                          <span className="text-xs text-zinc-600">|</span>
                          <span
                            className={`text-xs font-mono ${
                              (ev.communicationScore ?? 0) >= 7
                                ? 'text-emerald-400'
                                : (ev.communicationScore ?? 0) >= 4
                                  ? 'text-amber-400'
                                  : 'text-red-400'
                            }`}
                          >
                            C{ev.communicationScore}
                          </span>
                        </>
                      )}
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className={`h-4 w-4 text-zinc-600 transition ${
                          isOpen ? 'rotate-180' : ''
                        }`}
                      >
                        <path
                          fillRule="evenodd"
                          d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  </button>

                  {isOpen && (
                    <div className="space-y-3 border-t border-zinc-800 px-4 py-3 text-sm">
                      <div>
                        <div className="mb-1 text-xs text-zinc-500">
                          Question
                        </div>
                        <div className="text-zinc-300">
                          {turn.interviewerQuestion}
                        </div>
                      </div>

                      <div>
                        <div className="mb-1 text-xs text-zinc-500">
                          Your Response
                        </div>
                        <div className="rounded bg-zinc-800/50 p-2 text-zinc-400">
                          {turn.candidateResponse}
                        </div>
                      </div>

                      {ev && (
                        <>
                          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                            <span className="text-zinc-500">
                              Technical:{' '}
                              <span className="text-zinc-300">
                                {ev.technicalScore ?? '—'}
                              </span>
                            </span>
                            <span className="text-zinc-500">
                              Comm:{' '}
                              <span className="text-zinc-300">
                                {ev.communicationScore ?? '—'}
                              </span>
                            </span>
                            <span className="text-zinc-500">
                              Concise:{' '}
                              <span className="text-zinc-300">
                                {ev.concisenessScore ?? '—'}
                              </span>
                            </span>
                            <span className="text-zinc-500">
                              Confidence:{' '}
                              <span className="text-zinc-300">
                                {ev.confidenceScore ?? '—'}
                              </span>
                            </span>
                            <span className="text-zinc-500">
                              Code:{' '}
                              <span className="text-zinc-300">
                                {ev.codeQualityScore ?? '—'}
                              </span>
                            </span>
                            <span className="text-zinc-500">
                              STAR:{' '}
                              <span
                                className={
                                  ev.starFrameworkCheck
                                    ? 'text-emerald-400'
                                    : 'text-red-400'
                                }
                              >
                                {ev.starFrameworkCheck ? 'Yes' : 'No'}
                              </span>
                            </span>
                          </div>

                          {ev.constructiveCritique && (
                            <div>
                              <div className="mb-1 text-xs text-zinc-500">
                                Critique
                              </div>
                              <div className="rounded border border-amber-900/50 bg-amber-950/20 p-2 text-amber-300">
                                {ev.constructiveCritique}
                              </div>
                            </div>
                          )}

                          {Object.keys(ev.fillerWordsDetected).length > 0 && (
                            <div>
                              <div className="mb-1 text-xs text-zinc-500">
                                Filler Words
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {Object.entries(ev.fillerWordsDetected).map(
                                  ([word, count]) => (
                                    <span
                                      key={word}
                                      className="rounded bg-zinc-800 px-2 py-0.5 text-xs font-mono text-zinc-400"
                                    >
                                      {word} ({count})
                                    </span>
                                  ),
                                )}
                              </div>
                            </div>
                          )}
                        </>
                      )}

                      {!ev && (
                        <div className="text-xs text-zinc-600 italic">
                          Evaluation pending...
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}

function ScoreCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-zinc-100">{value}</div>
    </div>
  );
}
