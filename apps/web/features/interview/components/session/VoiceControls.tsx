"use client";

import { memo, useEffect, useRef } from "react";
import { Mic, MicOff, Loader2, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface VoiceControlsProps {
  isListening: boolean;
  isSupported: boolean;
  isDisabled: boolean;
  interimVolume: number;
  onToggle: () => void;
}

export const VoiceControls = memo(function VoiceControls({
  isListening,
  isSupported,
  isDisabled,
  interimVolume,
  onToggle,
}: VoiceControlsProps) {
  if (!isSupported) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground" title="Speech recognition not supported in this browser">
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
        disabled={isDisabled}
        onClick={onToggle}
        aria-label={isListening ? "Stop recording" : "Start recording"}
        className={cn(
          "relative h-10 w-10 transition-all",
          isListening && "bg-destructive text-destructive-foreground hover:bg-destructive/90 ring-4 ring-destructive/20",
        )}
      >
        {isListening ? (
          <>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex items-end gap-0.5 h-4">
                {[1, 2, 3].map((i) => (
                  <span
                    key={i}
                    className="w-0.5 bg-current rounded-full animate-pulse"
                    style={{
                      height: `${Math.max(20, Math.min(100, interimVolume * (i * 30)))}%`,
                      animationDelay: `${i * 0.15}s`,
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
      </Button>
      <span className="text-xs text-muted-foreground hidden sm:inline">
        {isListening ? "Recording..." : "Mic"}
      </span>
    </div>
  );
});
