import { createSupabaseServerClient, createServiceClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import { SessionList } from '@/frontend/components/dashboard/SessionList';
import { NewSessionButton } from '@/frontend/components/dashboard/NewSessionButton';
import type { SessionSummary } from '@/frontend/components/dashboard/SessionList';

export default async function DashboardPage() {
  let sessions: SessionSummary[] = [];
  let needsOnboarding = false;

  try {
    const supabase = await createSupabaseServerClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (user) {
      const db = createServiceClient();

      const { count } = await db
        .from('resume_embeddings')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id);

      if (!count || count === 0) {
        needsOnboarding = true;
      } else {
        const { data: rows } = await db
          .from('interview_sessions')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })
          .limit(50);

        sessions = (rows ?? []).map((r) => ({
          id: r.id,
          targetRole: r.target_role,
          difficulty: r.difficulty,
          currentStage: r.current_stage,
          isCompleted: r.is_completed,
          createdAt: r.created_at,
        }));
      }
    }
  } catch {
    // Not authenticated — show empty dashboard
  }

  if (needsOnboarding) redirect('/onboarding');

  return (
    <div className="min-h-screen bg-black text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800">
            <span className="text-sm font-bold text-emerald-400">T</span>
          </div>
          <h1 className="text-lg font-semibold">Dashboard</h1>
        </div>
        <NewSessionButton />
      </header>

      <main className="mx-auto max-w-3xl p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
          Practice Sessions
        </h2>
        <SessionList sessions={sessions} />
      </main>
    </div>
  );
}
