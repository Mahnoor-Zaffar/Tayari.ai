"use client";

import { memo } from "react";
import { Mic, MicOff, Radio, Loader2, AlertCircle, StopCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface VoiceControlsProps {
  isListening: boolean;
  isSpeaking: boolean;
  isReconnecting: boolean;
  isSupported: boolean;
  language: string;
  audioLevel: number;
  error: string | null;
  onToggle: () => void;
  onCancel: () => void;
}

export const VoiceControls = memo(function VoiceControls({
  isListening,
  isSpeaking,
  isReconnecting,
  isSupported,
  language,
  audioLevel,
  error,
  onToggle,
  onCancel,
}: VoiceControlsProps) {
  if (!isSupported) {
    return (
      <div
        className="flex items-center gap-2 text-xs text-muted-foreground"
        title="Speech recognition not supported in this browser"
      >
        <MicOff className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Mic unavailable</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant={isListening ? "default" : "outline"}
        size="icon"
        onClick={onToggle}
        disabled={isReconnecting}
        aria-label={isListening ? "Stop recording" : "Start recording"}
        className={cn(
          "relative h-10 w-10 transition-all",
          isListening &&
            "bg-destructive text-destructive-foreground hover:bg-destructive/90 ring-4 ring-destructive/20",
        )}
      >
        {isReconnecting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : isListening ? (
          <>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex items-end gap-0.5 h-4">
                {[1, 2, 3].map((i) => (
                  <span
                    key={i}
                    className="w-0.5 bg-current rounded-full"
                    style={{
                      height: isSpeaking ? `${Math.max(30, i * 25)}%` : "20%",
                      animation: isSpeaking ? `pulse 0.${3 + i}s ease-in-out infinite` : "none",
                    }}
                  />
                ))}
              </div>
            </div>
            <span className="sr-only">Recording</span>
          </>
        ) : (
          <Mic className="h-4 w-4" />
        )}
        {/* Language badge */}
        <span className="absolute -bottom-1 -right-1 rounded bg-muted px-1 py-px text-[9px] font-bold leading-none text-muted-foreground">
          {language.toUpperCase()}
        </span>
      </Button>

      {/* Cancel button — visible while speaking */}
      {isListening && isSpeaking && (
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={onCancel}
          aria-label="Cancel recording"
          className="h-8 w-8"
        >
          <StopCircle className="h-3.5 w-3.5" />
        </Button>
      )}

      {/* Audio level bar — visible while listening */}
      {isListening && !isReconnecting && (
        <div className="hidden sm:flex h-8 w-16 flex-col justify-center gap-0.5">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-green-500 transition-[width] duration-75"
              style={{ width: `${Math.min(100, Math.round(audioLevel * 100 * 2.5))}%` }}
            />
          </div>
        </div>
      )}

      <div className="hidden sm:flex flex-col">
        <span className="text-xs text-muted-foreground">
          {isReconnecting
            ? "Reconnecting..."
            : error
              ? "Voice error"
              : isListening
                ? isSpeaking
                  ? "Listening..."
                  : "Mic on"
                : "Mic"}
        </span>
        {isListening && !isReconnecting && (
          <span className="text-[10px] text-muted-foreground/70 flex items-center gap-1">
            <Radio className="h-2.5 w-2.5 text-green-400" />
            Deepgram
          </span>
        )}
        {error && !isReconnecting && (
          <span className="text-[10px] text-destructive flex items-center gap-1">
            <AlertCircle className="h-2.5 w-2.5" />
            <span className="max-w-[120px] truncate">{error}</span>
          </span>
        )}
      </div>
    </div>
  );
});
