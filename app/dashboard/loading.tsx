export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-black text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-zinc-800" />
          <div className="h-5 w-24 rounded bg-zinc-800" />
        </div>
        <div className="h-9 w-32 rounded-lg bg-zinc-800" />
      </header>

      <main className="mx-auto max-w-3xl p-6">
        <div className="mb-4 h-4 w-36 rounded bg-zinc-800" />

        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="mb-2 h-4 w-48 rounded bg-zinc-800" />
              <div className="h-3 w-32 rounded bg-zinc-800" />
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
