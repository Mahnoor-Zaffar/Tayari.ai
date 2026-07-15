"use client";

import { memo } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FullscreenToggleProps {
  isFullscreen: boolean;
  onToggle: () => void;
}

export const FullscreenToggle = memo(function FullscreenToggle({
  isFullscreen,
  onToggle,
}: FullscreenToggleProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={onToggle}
      aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
      className="h-8 w-8"
    >
      {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
    </Button>
  );
});
