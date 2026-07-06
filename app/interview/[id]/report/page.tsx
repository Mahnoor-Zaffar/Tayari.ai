import { createSupabaseServerClient } from '@/lib/supabase/server';
import { fetchSessionReport } from '@/backend/db/database';
import { ReportView } from './report-view';

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let sessionId = id;
  let userId: string;

  try {
    const supabase = await createSupabaseServerClient();
    const { data } = await supabase.auth.getSession();
    userId = data.session?.user?.id ?? '00000000-0000-0000-0000-000000000000';
  } catch {
    userId = '00000000-0000-0000-0000-000000000000';
  }

  let turns;

  try {
    turns = await fetchSessionReport(sessionId);
  } catch {
    turns = [];
  }

  const evaluated = turns.filter((t) => t.evaluation);

  const avgTechnical =
    evaluated.length > 0
      ? Math.round(
          (evaluated.reduce(
            (s, t) => s + (t.evaluation!.technicalScore ?? 0),
            0,
          ) /
            evaluated.length) *
            10,
        ) / 10
      : null;

  const avgCommunication =
    evaluated.length > 0
      ? Math.round(
          (evaluated.reduce(
            (s, t) => s + (t.evaluation!.communicationScore ?? 0),
            0,
          ) /
            evaluated.length) *
            10,
        ) / 10
      : null;

  const starCount = evaluated.filter(
    (t) => t.evaluation?.starFrameworkCheck,
  ).length;

  const starRate =
    evaluated.length > 0
      ? Math.round((starCount / evaluated.length) * 100)
      : null;

  const totalFillerWords = evaluated.reduce((s, t) => {
    const fw = t.evaluation?.fillerWordsDetected ?? {};
    return s + Object.values(fw).reduce((a, b) => a + b, 0);
  }, 0);

  return (
    <ReportView
      sessionId={sessionId}
      turns={turns}
      aggregate={{
        avgTechnical,
        avgCommunication,
        starRate,
        totalTurns: turns.length,
        totalFillerWords,
      }}
    />
  );
}
