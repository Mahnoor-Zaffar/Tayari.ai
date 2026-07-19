"use client";

import { use, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { InterviewSession } from "@/features/interview/components/session/InterviewSession";
import { CodingInterviewLayout } from "@/features/coding/components/CodingInterviewLayout";
import { SystemDesignLayout } from "@/features/interview/components/whiteboard/SystemDesignLayout";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { interviewSetupApi } from "@/features/interview/api/interview-setup";

interface SessionData {
  session_id: string;
  interview_id: string;
  status: string;
  initial_question: string;
  duration_minutes: number;
  interview_type: string;
}

const SESSION_KEY = "tayari_active_session";

export default function InterviewRoomPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { user, accessToken, isLoading: authLoading } = useAuth();
  const [session, setSession] = useState<SessionData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const handleComplete = useCallback(() => {
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch {
      /* ignore */
    }
    setTimeout(() => router.push(`/dashboard/interview/${id}/evaluation`), 2000);
  }, [id, router]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/auth/login");
      return;
    }

    const startInterview = async () => {
      try {
        const stored = typeof window !== "undefined" ? localStorage.getItem(SESSION_KEY) : null;
        if (stored) {
          try {
            const parsed = JSON.parse(stored) as SessionData;
            if (parsed.interview_id === id) {
              const status = await interviewSetupApi.getSessionStatus(parsed.session_id);
              if (status?.state && !["completed", "failed", "archived"].includes(status.state)) {
                setSession(parsed);
                setLoading(false);
                return;
              }
            }
          } catch {
            /* stored session is invalid */
          }
        }

        const interview = await interviewSetupApi.get(id);
        const result = await interviewSetupApi.startSession(interview.id);
        const sessionData: SessionData = {
          session_id: result.session_id,
          interview_id: result.interview_id,
          status: result.status,
          initial_question: result.initial_question,
          duration_minutes: interview.duration_minutes ?? 30,
          interview_type: interview.type,
        };
        try {
          localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
        } catch {
          /* ignore */
        }
        setSession(sessionData);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to start interview";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    startInterview();
  }, [id, user, authLoading, router]);

  if (authLoading || loading) return <InterviewRoomSkeleton />;

  if (error) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-destructive">Failed to start interview</h2>
          <p className="mt-1 text-sm text-muted-foreground">{error}</p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 text-sm text-primary underline underline-offset-2"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!session) return null;

  const isCoding = session.interview_type === "coding";
  const isSystemDesign = session.interview_type === "system-design";

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col p-2 sm:p-4">
      {isCoding ? (
        <CodingInterviewLayout
          sessionId={session.session_id}
          interviewId={session.interview_id}
          token={accessToken ?? ""}
          durationMinutes={session.duration_minutes}
          onComplete={handleComplete}
        />
      ) : isSystemDesign ? (
        <SystemDesignLayout
          sessionId={session.session_id}
          interviewId={session.interview_id}
          token={accessToken ?? ""}
          durationMinutes={session.duration_minutes}
          onComplete={handleComplete}
        />
      ) : (
        <InterviewSession
          sessionId={session.session_id}
          interviewId={session.interview_id}
          token={accessToken ?? ""}
          durationMinutes={session.duration_minutes}
          onComplete={handleComplete}
        />
      )}
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
