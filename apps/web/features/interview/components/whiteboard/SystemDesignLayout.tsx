"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { PauseIcon, Square, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useInterviewSession } from "@/features/interview/hooks/use-interview-session";
import { Whiteboard } from "@/features/interview/components/whiteboard/Whiteboard";
import { SessionTimer } from "@/features/interview/components/session/SessionTimer";
import { SessionConnectionStatus } from "@/features/interview/components/session/ConnectionStatus";
import { LiveTranscript } from "@/features/interview/components/session/LiveTranscript";

interface SystemDesignLayoutProps {
  sessionId: string;
  interviewId: string;
  token: string;
  durationMinutes?: number;
  onComplete?: (sessionId: string) => void;
  className?: string;
}

export function SystemDesignLayout({
  sessionId, interviewId, token, durationMinutes = 30, onComplete, className,
}: SystemDesignLayoutProps) {
  const session = useInterviewSession({ sessionId, interviewId, token, durationMinutes, onComplete });
  const isActive = session.state.state === "active";
  const isPaused = session.state.state === "paused";

  return (
    <div className={cn("flex h-full flex-col overflow-hidden rounded-xl border border-border bg-background", className)}>
      {/* Top Bar */}
      <header className="flex items-center justify-between border-b border-border px-3 py-1.5">
        <div className="flex items-center gap-2">
          <SessionConnectionStatus status={session.state.connectionStatus} />
          <span className="text-xs font-medium text-muted-foreground">System Design</span>
        </div>
        <SessionTimer
          remainingSeconds={session.timer.remaining}
          elapsedSeconds={session.timer.elapsed}
          isPaused={isPaused}
          state={session.state.state}
        />
        <div className="flex items-center gap-1">
          {isActive && (
            <Button type="button" variant="ghost" size="sm" onClick={session.pauseSession} aria-label="Pause">
              <PauseIcon className="h-4 w-4" />
            </Button>
          )}
          <Button type="button" variant="ghost" size="sm" onClick={() => {
            session.endSession();
            onComplete?.(sessionId);
          }} aria-label="End">
            <Square className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main: Chat + Whiteboard */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat Transcript */}
        <div className="flex w-72 flex-shrink-0 flex-col overflow-hidden border-r border-border bg-card">
          <div className="flex items-center gap-2 border-b border-border px-3 py-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Transcript</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <LiveTranscript transcript={session.state.transcript} />
          </div>
        </div>

        {/* Whiteboard */}
        <div className="flex flex-1 flex-col">
          <Whiteboard />
        </div>
      </div>
    </div>
  );
}
