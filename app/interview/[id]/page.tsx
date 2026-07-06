import { createSupabaseServerClient } from '@/lib/supabase/server';
import { InterviewView } from './interview-view';

export default async function InterviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let userId: string;

  try {
    const supabase = await createSupabaseServerClient();
    const { data } = await supabase.auth.getSession();
    userId = data.session?.user?.id ?? '00000000-0000-0000-0000-000000000000';
  } catch {
    userId = '00000000-0000-0000-0000-000000000000';
  }

  return <InterviewView userId={userId} />;
}
