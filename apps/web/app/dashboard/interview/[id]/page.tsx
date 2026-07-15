"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { InterviewSession } from "@/features/interview/components/session/InterviewSession";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { interviewSetupApi } from "@/features/interview/api/interview-setup";

export default function InterviewRoomPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [interview, setInterview] = useState<{ id: string; type: string; duration_minutes: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/auth/login");
      return;
    }
    const fetchInterview = async () => {
      try {
        const data = await interviewSetupApi.get(id);
        setInterview({
          id: data.id,
          type: data.type,
          duration_minutes: data.duration_minutes ?? 30,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load interview");
      } finally {
        setLoading(false);
      }
    };
    fetchInterview();
  }, [id, user, authLoading, router]);

  if (authLoading || loading) {
    return <InterviewRoomSkeleton />;
  }

  if (error) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-destructive">Failed to load interview</h2>
          <p className="mt-1 text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  if (!interview) return null;

  // Use the interview ID as the session ID for now
  // In production, start a session via POST /sessions first
  const sessionId = interview.id;
  const token = ""; // Will come from auth context

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col p-2 sm:p-4">
      <InterviewSession
        sessionId={sessionId}
        interviewId={interview.id}
        token={token}
        durationMinutes={interview.duration_minutes}
      />
    </div>
  );
}

function InterviewRoomSkeleton() {
  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col gap-4 p-4">
      <div className="h-14 animate-skeleton rounded-lg bg-muted" />
      <div className="flex flex-1 gap-4">
        <div className="flex-1 animate-skeleton rounded-lg bg-muted" />
        <div className="hidden w-72 animate-skeleton rounded-lg bg-muted sm:block" />
      </div>
    </div>
  );
}
