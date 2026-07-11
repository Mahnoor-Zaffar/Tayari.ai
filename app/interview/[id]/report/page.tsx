import { fetchSessionReport, type TurnWithEvaluation } from '@/backend/db/database';
import { computeAggregate } from '@/backend/services/report-aggregate';
import { ReportView } from './report-view';

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const sessionId = id;

  let turns: TurnWithEvaluation[];

  try {
    turns = await fetchSessionReport(sessionId);
  } catch {
    turns = [];
  }

  return (
    <ReportView
      sessionId={sessionId}
      turns={turns}
      aggregate={computeAggregate(turns)}
    />
  );
}
