"use client";

import { memo, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Mic, Square, Loader2, AlertTriangle, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ConnectionStatus as WSConnectionStatus } from "@/features/interview/lib/session-types";

interface AnswerInputProps {
  isAiThinking: boolean;
  connectionStatus: WSConnectionStatus;
  isPaused: boolean;
  liveTranscript?: string;
  isListening?: boolean;
  voiceError?: string | null;
  isVoiceReconnecting?: boolean;
  onAnswer: (text: string) => void;
  onRequestHint: () => void;
}

export const AnswerInput = memo(function AnswerInput({
  isAiThinking,
  connectionStatus,
  isPaused,
  liveTranscript = "",
  isListening = false,
  voiceError = null,
  isVoiceReconnecting = false,
  onAnswer,
  onRequestHint,
}: AnswerInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const isDisabled = isAiThinking || connectionStatus !== "connected" || isPaused;

  useEffect(() => {
    if (!isDisabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isDisabled]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const text = inputRef.current?.value.trim();
      if (text) {
        onAnswer(text);
        if (inputRef.current) inputRef.current.value = "";
      }
    }
  };

  const showVoiceError = voiceError && !isVoiceReconnecting;

  return (
    <div className="space-y-2">
      {/* Voice error banner */}
      {showVoiceError && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive"
        >
          <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
          <span>Voice unavailable — type your answer below</span>
        </motion.div>
      )}

      {/* Voice reconnecting banner */}
      {isVoiceReconnecting && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 rounded-md border border-muted bg-muted/30 px-3 py-2 text-xs text-muted-foreground"
        >
          <WifiOff className="h-3.5 w-3.5 flex-shrink-0 animate-pulse" />
          <span>Reconnecting voice...</span>
        </motion.div>
      )}

      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <textarea
            ref={inputRef}
            disabled={isDisabled}
            onKeyDown={handleKeyDown}
            placeholder={
              isPaused
                ? "Interview paused — press Resume to continue"
                : isAiThinking
                  ? "AI is thinking..."
                  : isListening
                    ? "Speak now — live transcription..."
                    : voiceError
                      ? "Type your answer here (voice unavailable)"
                      : "Type your answer here... (or click the mic)"
            }
            value={isListening && liveTranscript ? liveTranscript : undefined}
            rows={2}
            className={cn(
              "w-full resize-none rounded-lg border border-input bg-background px-2.5 py-2 text-xs sm:px-3 sm:py-2.5 sm:text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
            )}
            aria-label="Your answer"
          />
          {isAiThinking && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <Loader2 className="h-4 w-4 animate-spin text-info" />
            </div>
          )}
        </div>
        <Button
          type="button"
          size="icon"
          variant="outline"
          disabled={isDisabled}
          onClick={() => {
            const text = inputRef.current?.value.trim();
            if (text) {
              onAnswer(text);
              if (inputRef.current) inputRef.current.value = "";
            }
          }}
          aria-label="Send answer"
        >
          <Square className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {isDisabled
            ? isPaused
              ? "Paused"
              : isAiThinking
                ? "Waiting for AI..."
                : "Connecting..."
            : "Enter to send · Shift+Enter for newline"}
        </span>
        <button
          type="button"
          onClick={onRequestHint}
          disabled={isDisabled}
          className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground disabled:opacity-50"
        >
          Need a hint?
        </button>
      </div>
    </div>
  );
});
