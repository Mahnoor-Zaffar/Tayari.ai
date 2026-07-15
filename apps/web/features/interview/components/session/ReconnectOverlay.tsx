"use client";

import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { WifiOff, RefreshCw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ConnectionStatus as WSConnectionStatus } from "@/features/interview/lib/session-types";

interface ReconnectOverlayProps {
  status: WSConnectionStatus;
  onReconnect: () => void;
}

export const ReconnectOverlay = memo(function ReconnectOverlay({
  status,
  onReconnect,
}: ReconnectOverlayProps) {
  const show = status === "disconnected" || status === "reconnecting";

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
          aria-label="Connection lost"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="flex flex-col items-center gap-4 text-center"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
              <WifiOff className="h-8 w-8 text-destructive" />
            </div>
            <h2 className="text-xl font-bold">Connection Lost</h2>
            <p className="max-w-sm text-sm text-muted-foreground">
              {status === "reconnecting"
                ? "Attempting to reconnect..."
                : "Your internet connection dropped. We'll save your progress and you can rejoin."}
            </p>
            {status === "disconnected" && (
              <Button type="button" size="lg" onClick={onReconnect} className="mt-2">
                <RefreshCw className="h-4 w-4" /> Reconnect
              </Button>
            )}
            {status === "reconnecting" && (
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
