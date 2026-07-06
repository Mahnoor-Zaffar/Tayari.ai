export default function ReportLoading() {
  return (
    <div className="min-h-screen bg-black p-6 text-zinc-100">
      <div className="mx-auto max-w-4xl animate-pulse">
        <div className="mb-8 h-8 w-48 rounded bg-zinc-800" />

        <div className="mb-8 grid grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-zinc-800 p-4">
              <div className="mb-2 h-3 w-16 rounded bg-zinc-800" />
              <div className="mb-1 h-8 w-20 rounded bg-zinc-700" />
              <div className="h-3 w-24 rounded bg-zinc-800" />
            </div>
          ))}
        </div>

        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-zinc-800 p-4">
              <div className="mb-2 h-3 w-32 rounded bg-zinc-800" />
              <div className="h-4 w-full rounded bg-zinc-800" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
