'use client';

export default function InterviewError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-black px-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-900/50">
        <span className="text-2xl text-red-400">!</span>
      </div>
      <h2 className="text-lg font-semibold text-zinc-200">Interview Error</h2>
      <p className="max-w-sm text-center text-sm text-zinc-500">
        {error.message || 'The interview session encountered an error.'}
      </p>
      <button
        onClick={reset}
        className="rounded-lg bg-zinc-800 px-5 py-2 text-sm font-medium text-zinc-200 transition-colors hover:bg-zinc-700"
      >
        Retry
      </button>
    </div>
  );
}
