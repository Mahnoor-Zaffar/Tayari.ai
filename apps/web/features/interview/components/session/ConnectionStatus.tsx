"use client";

import { memo } from "react";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ConnectionStatus as WSConnectionStatus } from "@/features/interview/lib/session-types";

interface ConnectionStatusProps {
  status: WSConnectionStatus;
}

export const SessionConnectionStatus = memo(function SessionConnectionStatus({
  status,
}: ConnectionStatusProps) {
  const config = {
    connected: { icon: Wifi, text: "Connected", className: "text-success" },
    connecting: { icon: Loader2, text: "Connecting", className: "text-info" },
    reconnecting: { icon: Loader2, text: "Reconnecting", className: "text-warning" },
    disconnected: { icon: WifiOff, text: "Disconnected", className: "text-destructive" },
  }[status];

  const Icon = config.icon;

  return (
    <div
      className={cn("flex items-center gap-1.5 text-xs font-medium", config.className)}
      role="status"
      aria-label={`Connection: ${config.text}`}
    >
      <Icon className={cn("h-3 w-3", status === "reconnecting" && "animate-spin")} />
      <span className="hidden sm:inline">{config.text}</span>
    </div>
  );
});
