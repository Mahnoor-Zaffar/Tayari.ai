"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { authApi } from "@/lib/api/auth";
import { useAuth } from "@/features/auth/hooks/use-auth";

export default function AuthCallbackPage() {
  const router = useRouter();
  const { setSession } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function handleCallback() {
      if (!supabase) {
        setError("Supabase is not configured");
        return;
      }

      const { data, error } = await supabase.auth.getSession();
      if (error || !data.session) {
        setError(error?.message ?? "No session returned");
        return;
      }

      const provider = (data.session.user.app_metadata?.provider ?? "google") as
        "google" | "github";
      const result = await authApi.socialLogin({
        provider,
        access_token: data.session.access_token,
      });

      setSession(result.access_token, result.refresh_token, result.user);
      router.push("/dashboard");
    }
    handleCallback().catch((err) => setError(err.message));
  }, [router, setSession]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-destructive">Authentication failed: {error}</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Completing sign in…</p>
    </div>
  );
}
