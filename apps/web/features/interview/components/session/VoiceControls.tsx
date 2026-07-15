"use client";

import { memo, useRef, useEffect } from "react";
import { Mic, MicOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface VoiceControlsProps {
  isActive: boolean;
  isMuted: boolean;
  isDisabled: boolean;
  onToggleMute: () => void;
}

export const VoiceControls = memo(function VoiceControls({
  isActive,
  isMuted,
  isDisabled,
  onToggleMute,
}: VoiceControlsProps) {
  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant={isMuted ? "outline" : "default"}
        size="icon"
        disabled={isDisabled}
        onClick={onToggleMute}
        aria-label={isMuted ? "Unmute microphone" : "Mute microphone"}
        className={cn(
          "relative h-10 w-10 transition-all",
          isActive && !isMuted && "ring-4 ring-primary/20",
        )}
      >
        {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
      </Button>
    </div>
  );
});
