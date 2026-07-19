"use client";

import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { WifiOff, RefreshCw, Loader2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ConnectionStatus as WSConnectionStatus } from "@/features/interview/lib/session-types";

interface ReconnectOverlayProps {
  status: WSConnectionStatus;
  error?: string | null;
  onReconnect: () => void;
}

export const ReconnectOverlay = memo(function ReconnectOverlay({
  status,
  error,
  onReconnect,
}: ReconnectOverlayProps) {
  const show = status === "disconnected" || status === "reconnecting";

  const isSessionNotFound = error?.includes("Session not found");

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 z-50 flex items-center justify-center rounded-xl bg-background/80 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label={isSessionNotFound ? "Session expired" : "Connection lost"}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="flex flex-col items-center gap-4 text-center"
          >
            <div
              className={`flex h-16 w-16 items-center justify-center rounded-full ${isSessionNotFound ? "bg-yellow-500/10" : "bg-destructive/10"}`}
            >
              {isSessionNotFound ? (
                <AlertTriangle className="h-8 w-8 text-yellow-500" />
              ) : (
                <WifiOff className="h-8 w-8 text-destructive" />
              )}
            </div>
            <h2 className="text-xl font-bold">
              {isSessionNotFound ? "Session Expired" : "Connection Lost"}
            </h2>
            <p className="max-w-sm text-sm text-muted-foreground">
              {isSessionNotFound
                ? "This interview session has expired or was lost. Please start a new interview from the dashboard."
                : status === "reconnecting"
                  ? "Attempting to reconnect..."
                  : "Your connection dropped. You can try to rejoin."}
            </p>
            {isSessionNotFound ? (
              <Button
                type="button"
                size="lg"
                variant="outline"
                onClick={() => (window.location.href = "/dashboard/interviews")}
                className="mt-2"
              >
                Back to Interviews
              </Button>
            ) : status === "disconnected" ? (
              <Button type="button" size="lg" onClick={onReconnect} className="mt-2">
                <RefreshCw className="h-4 w-4" /> Reconnect
              </Button>
            ) : (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Reconnecting...
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
});
