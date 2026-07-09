import { createSupabaseServerClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import { ResumeUploader } from '@/frontend/components/onboarding/ResumeUploader';

export default async function OnboardingPage() {
  try {
    const supabase = await createSupabaseServerClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (user) {
      const { count } = await supabase
        .from('resume_embeddings')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id);

      if (count && count > 0) {
        redirect('/dashboard');
      }
    }
  } catch {
    // Not authenticated — show onboarding anyway
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-black px-4">
      <div className="flex flex-col items-center gap-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-800">
            <span className="text-lg font-bold text-emerald-400">T</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Tayari.ai</h1>
        </div>

        <div className="text-center">
          <h2 className="text-lg font-semibold text-zinc-100">
            Welcome! Let&apos;s start with your resume
          </h2>
          <p className="mt-1 text-sm text-zinc-500">
            Upload your resume so the interviewer can ask personalised questions
          </p>
        </div>

        <ResumeUploader />
      </div>
    </div>
  );
}
