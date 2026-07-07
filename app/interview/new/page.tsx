import { createSupabaseServerClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import { NewInterviewForm } from './form';

export default async function NewInterviewPage() {
  const supabase = await createSupabaseServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login');
  }

  const { count } = await supabase
    .from('resume_embeddings')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', user.id);

  if (!count || count === 0) {
    redirect('/onboarding');
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-black px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-white">New Interview</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Configure your practice session
          </p>
        </div>
        <NewInterviewForm />
      </div>
    </div>
  );
}
