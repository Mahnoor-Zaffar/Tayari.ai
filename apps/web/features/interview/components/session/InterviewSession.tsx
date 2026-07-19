"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { PauseIcon, Play, Square, FileText, Menu, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useInterviewSession } from "@/features/interview/hooks/use-interview-session";
import { useFullscreen } from "@/features/interview/hooks/use-fullscreen";
import { useKeyboardShortcuts } from "@/features/interview/hooks/use-keyboard-shortcuts";
import { useNotes } from "@/features/interview/hooks/use-notes";
import { SessionTimer } from "./SessionTimer";
import { SessionConnectionStatus } from "./ConnectionStatus";
import { ProgressIndicator } from "./ProgressIndicator";
import { FullscreenToggle } from "./FullscreenToggle";
import { VoiceControls } from "./VoiceControls";
import { useStreamingRecognition } from "@/features/interview/hooks/use-streaming-recognition";
import { PauseOverlay } from "./PauseOverlay";
import { ReconnectOverlay } from "./ReconnectOverlay";
import { EndInterviewDialog } from "./EndInterviewDialog";
import { NotesPanel } from "./NotesPanel";
import { ConversationArea } from "./ConversationArea";

interface InterviewSessionProps {
  sessionId: string;
  interviewId: string;
  token: string;
  durationMinutes?: number;
  className?: string;
  onComplete?: (sessionId: string) => void;
}

export function InterviewSession({
  sessionId,
  interviewId,
  token,
  durationMinutes = 30,
  className,
  onComplete,
}: InterviewSessionProps) {
  const {
    state,
    timer,
    sendAnswer,
    pauseSession,
    resumeSession,
    requestHint,
    endSession,
    reconnect,
  } = useInterviewSession({
    sessionId,
    interviewId,
    token,
    durationMinutes,
    onComplete,
  });

  const { isFullscreen, toggle: toggleFullscreen } = useFullscreen();
  const { notes, setNotes } = useNotes(interviewId);
  const [showEndDialog, setShowEndDialog] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const speech = useStreamingRecognition(token);
  const prevTranscriptRef = useRef("");
  const [interimVolume] = useState(0.5);

  useEffect(() => {
    if (speech.isListening) return;
    const newText = speech.transcript.slice(prevTranscriptRef.current.length).trim();
    if (newText) {
      sendAnswer(newText);
      prevTranscriptRef.current = speech.transcript;
    }
  }, [speech.isListening, speech.transcript, sendAnswer]);

  useEffect(() => {
    prevTranscriptRef.current = "";
  }, [sessionId]);

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      key: "p",
      ctrl: true,
      handler: state.state === "paused" ? resumeSession : pauseSession,
      enabled: state.state === "active" || state.state === "paused",
    },
    {
      key: "e",
      ctrl: true,
      handler: () => setShowEndDialog(true),
      enabled: state.state === "active" || state.state === "paused",
    },
    { key: "n", ctrl: true, handler: () => setShowNotes((v) => !v) },
    { key: "f", ctrl: true, handler: toggleFullscreen },
    { key: "h", ctrl: true, handler: () => requestHint() },
    { key: "m", ctrl: true, handler: () => speech.toggle() },
  ]);

  const handleEndConfirm = useCallback(() => {
    setShowEndDialog(false);
    endSession();
  }, [endSession]);

  const isActive = state.state === "active";
  const isPaused = state.state === "paused";

  return (
    <div
      className={cn(
        "relative flex h-full flex-col overflow-hidden rounded-xl border border-border bg-background",
        className,
      )}
    >
      {/* ── Top Bar ───────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="flex items-center gap-3">
          <SessionConnectionStatus status={state.connectionStatus} />
          <span className="hidden text-xs text-muted-foreground sm:inline">
            {state.state === "completed"
              ? "Completed"
              : state.state === "completing"
                ? "Wrapping up..."
                : ""}
          </span>
        </div>

        <SessionTimer
          remainingSeconds={timer.remaining}
          elapsedSeconds={timer.elapsed}
          isPaused={isPaused}
          state={state.state}
        />

        <div className="flex items-center gap-1">
          <FullscreenToggle isFullscreen={isFullscreen} onToggle={toggleFullscreen} />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 sm:hidden"
            onClick={() => setShowMobileMenu((v) => !v)}
            aria-label="Menu"
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* ── Mobile Controls ────────────────────────────────────────────── */}
      {showMobileMenu && (
        <div className="flex items-center gap-2 border-b border-border px-4 py-2 sm:hidden">
          <MobileControls
            isActive={isActive}
            isPaused={isPaused}
            state={state.state}
            showNotes={showNotes}
            onPause={pauseSession}
            onResume={resumeSession}
            onEnd={() => setShowEndDialog(true)}
            onNotes={() => setShowNotes((v) => !v)}
          />
        </div>
      )}

      {/* ── Desktop Controls Bar ────────────────────────────────────────── */}
      <div className="hidden items-center justify-between border-b border-border px-4 py-1.5 sm:flex">
        <div className="flex items-center gap-1">
          <VoiceControls
            isListening={speech.isListening}
            isSupported={speech.isSupported}
            isDisabled={state.connectionStatus !== "connected"}
            interimVolume={interimVolume}
            source={speech.source}
            latencyMs={speech.latencyMs}
            onToggle={speech.toggle}
          />
        </div>

        <div className="flex items-center gap-1">
          <ProgressIndicator current={state.questions.length} total={state.questions.length} />
        </div>

        <div className="flex items-center gap-1">
          {isActive && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={pauseSession}
              aria-label="Pause interview"
            >
              <PauseIcon className="h-4 w-4" /> <span className="hidden lg:inline">Pause</span>
            </Button>
          )}
          {isPaused && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={resumeSession}
              aria-label="Resume interview"
            >
              <Play className="h-4 w-4" /> <span className="hidden lg:inline">Resume</span>
            </Button>
          )}
          {!state.state.includes("completed") && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowEndDialog(true)}
              aria-label="End interview"
            >
              <Square className="h-4 w-4" /> <span className="hidden lg:inline">End</span>
            </Button>
          )}
          <Button
            type="button"
            variant={showNotes ? "default" : "ghost"}
            size="sm"
            onClick={() => setShowNotes((v) => !v)}
            aria-label="Toggle notes panel"
          >
            <FileText className="h-4 w-4" /> <span className="hidden lg:inline">Notes</span>
          </Button>
        </div>
      </div>

      {/* ── Main Content ──────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        <ConversationArea
          questions={state.questions}
          transcript={state.transcript}
          isAiThinking={state.isAiThinking}
          connectionStatus={state.connectionStatus}
          isPaused={isPaused}
          liveTranscript={speech.interimTranscript}
          isListening={speech.isListening}
          onAnswer={sendAnswer}
          onRequestHint={requestHint}
          className="flex-1"
        />

        {/* Notes Panel (desktop) */}
        {showNotes && (
          <div className="hidden w-72 flex-shrink-0 sm:block">
            <NotesPanel
              isOpen={true}
              onClose={() => setShowNotes(false)}
              notes={notes}
              onNotesChange={setNotes}
            />
          </div>
        )}
      </div>

      {/* ── Overlays ──────────────────────────────────────────────────── */}
      <PauseOverlay isPaused={isPaused} onResume={resumeSession} />
      <ReconnectOverlay
        status={state.connectionStatus}
        error={state.error}
        onReconnect={reconnect}
      />
      <EndInterviewDialog
        isOpen={showEndDialog}
        onClose={() => setShowEndDialog(false)}
        onConfirm={handleEndConfirm}
      />

      {/* ── Completed State ──────────────────────────────────────────── */}
      {state.state === "completed" && (
        <div className="absolute inset-0 z-40 flex items-center justify-center rounded-xl bg-background/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-success/10">
              <ChevronRight className="h-8 w-8 text-success" />
            </div>
            <h2 className="text-xl font-bold">Interview Complete</h2>
            <p className="max-w-sm text-sm text-muted-foreground">
              Your evaluation is being prepared. You&apos;ll be redirected shortly.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Mobile Controls Sub-component ─────────────────────────────────────────────

function MobileControls({
  isActive,
  isPaused,
  state,
  showNotes,
  onPause,
  onResume,
  onEnd,
  onNotes,
}: {
  isActive: boolean;
  isPaused: boolean;
  state: string;
  showNotes: boolean;
  onPause: () => void;
  onResume: () => void;
  onEnd: () => void;
  onNotes: () => void;
}) {
  return (
    <div className="flex w-full items-center justify-between">
      {isActive && (
        <Button type="button" variant="ghost" size="sm" onClick={onPause}>
          <PauseIcon className="h-4 w-4" /> Pause
        </Button>
      )}
      {isPaused && (
        <Button type="button" variant="ghost" size="sm" onClick={onResume}>
          <Play className="h-4 w-4" /> Resume
        </Button>
      )}
      {!state.includes("completed") && (
        <Button type="button" variant="ghost" size="sm" onClick={onEnd}>
          <Square className="h-4 w-4" /> End
        </Button>
      )}
      <Button type="button" variant={showNotes ? "default" : "ghost"} size="sm" onClick={onNotes}>
        <FileText className="h-4 w-4" /> Notes
      </Button>
    </div>
  );
}
