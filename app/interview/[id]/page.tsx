import { createClient } from '@supabase/supabase-js';
import { redirect, notFound } from 'next/navigation';
import { InterviewView } from './interview-view';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
);

export default async function InterviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const { data: session } = await supabase
    .from('interview_sessions')
    .select('id, is_completed')
    .eq('id', id)
    .single();

  if (!session) {
    notFound();
  }

  if (session.is_completed) {
    redirect(`/interview/${id}/report`);
  }

  return <InterviewView />;
}
