"use client";

import { memo } from "react";
import { cn } from "@/lib/utils";

interface SessionTimerProps {
  remainingSeconds: number;
  elapsedSeconds: number;
  isPaused: boolean;
  state: string;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export const SessionTimer = memo(function SessionTimer({
  remainingSeconds,
  elapsedSeconds,
  isPaused,
  state,
}: SessionTimerProps) {
  const isLow = remainingSeconds <= 300;
  const isCritical = remainingSeconds <= 60;

  return (
    <div className="flex items-center gap-4" role="timer" aria-label="Interview timer">
      <div className="text-center">
        <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          Elapsed
        </p>
        <p className="text-lg font-mono font-bold tabular-nums">
          {formatTime(elapsedSeconds)}
        </p>
      </div>
      <div className="text-center">
        <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          Remaining
        </p>
        <p
          className={cn(
            "text-lg font-mono font-bold tabular-nums transition-colors",
            isCritical && "text-destructive animate-pulse",
            isLow && !isCritical && "text-warning",
            !isLow && "text-foreground",
          )}
        >
          {isPaused ? "—:—" : formatTime(remainingSeconds)}
        </p>
      </div>
      <div className="w-32">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-1000",
              isCritical && "bg-destructive",
              isLow && !isCritical && "bg-warning",
              !isLow && "bg-primary",
            )}
            style={{
              width: `${Math.max(0, (remainingSeconds / (remainingSeconds + elapsedSeconds || 1)) * 100)}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
});
