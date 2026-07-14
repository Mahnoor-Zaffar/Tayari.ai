"use client";

import { memo, useEffect, useState, useCallback } from "react";
import {
  Mic,
  Camera,
  Volume2,
  Globe,
  Wifi,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  RotateCcw,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useDeviceCheck } from "@/features/interview/hooks/use-interview-setup";
import type { LucideIcon } from "lucide-react";

type CheckState = "pending" | "checking" | "passed" | "failed";

interface CheckItem {
  key: string;
  label: string;
  icon: LucideIcon;
  description: string;
  state: CheckState;
  detail?: string;
}

interface DeviceCheckStepProps {
  className?: string;
  onChecksComplete?: (allPassed: boolean) => void;
}

export const DeviceCheckStep = memo(function DeviceCheckStep({
  className,
  onChecksComplete,
}: DeviceCheckStepProps) {
  const deviceCheckMutation = useDeviceCheck();
  const [items, setItems] = useState<CheckItem[]>([
    {
      key: "microphone",
      label: "Microphone",
      icon: Mic,
      description: "Required for voice interview",
      state: "pending",
    },
    {
      key: "camera",
      label: "Camera",
      icon: Camera,
      description: "Optional (for video interviews)",
      state: "pending",
    },
    {
      key: "speaker",
      label: "Speaker",
      icon: Volume2,
      description: "Required to hear the interviewer",
      state: "pending",
    },
    {
      key: "browser",
      label: "Browser Compatibility",
      icon: Globe,
      description: "Checks your browser supports required APIs",
      state: "pending",
    },
  ]);
  const [connectionState, setConnectionState] = useState<"checking" | "good" | "poor" | "offline">(
    "checking",
  );
  const [hasRun, setHasRun] = useState(false);

  const updateItem = useCallback((key: string, updates: Partial<CheckItem>) => {
    setItems((prev) => prev.map((item) => (item.key === key ? { ...item, ...updates } : item)));
  }, []);

  const checkMicrophone = useCallback(async (): Promise<boolean> => {
    updateItem("microphone", { state: "checking", detail: undefined });
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());
      updateItem("microphone", { state: "passed" });
      return true;
    } catch {
      updateItem("microphone", {
        state: "failed",
        detail: "Microphone access denied or unavailable",
      });
      return false;
    }
  }, [updateItem]);

  const checkCamera = useCallback(async (): Promise<boolean> => {
    updateItem("camera", { state: "checking", detail: undefined });
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      stream.getTracks().forEach((t) => t.stop());
      updateItem("camera", { state: "passed" });
      return true;
    } catch {
      updateItem("camera", { state: "failed", detail: "Camera not available (optional)" });
      return false;
    }
  }, [updateItem]);

  const checkSpeaker = useCallback(async (): Promise<boolean> => {
    updateItem("speaker", { state: "checking", detail: undefined });
    try {
      const audio = new Audio();
      audio.volume = 0;
      await audio.play();
      audio.pause();
      updateItem("speaker", { state: "passed" });
      return true;
    } catch {
      if ("speaker" in navigator) {
        updateItem("speaker", { state: "passed", detail: "Speaker available" });
        return true;
      }
      updateItem("speaker", { state: "passed" });
      return true;
    }
  }, [updateItem]);

  const checkBrowser = useCallback(async (): Promise<boolean> => {
    updateItem("browser", { state: "checking", detail: undefined });
    const hasMediaDevices = !!navigator.mediaDevices;
    const hasGetUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    const hasRTCPeerConnection = typeof RTCPeerConnection !== "undefined";
    const hasWebAudio = !!(
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    );

    if (hasMediaDevices && hasGetUserMedia && hasRTCPeerConnection && hasWebAudio) {
      updateItem("browser", { state: "passed" });
      return true;
    } else {
      const missing: string[] = [];
      if (!hasMediaDevices) missing.push("MediaDevices");
      if (!hasGetUserMedia) missing.push("getUserMedia");
      if (!hasRTCPeerConnection) missing.push("WebRTC");
      if (!hasWebAudio) missing.push("Web Audio");
      updateItem("browser", { state: "failed", detail: `Missing: ${missing.join(", ")}` });
      return false;
    }
  }, [updateItem]);

  const checkConnection = useCallback(async (): Promise<void> => {
    setConnectionState("checking");
    try {
      const start = performance.now();
      const resp = await fetch("/api/health", { method: "HEAD", cache: "no-store" });
      const latency = performance.now() - start;
      if (!resp.ok && resp.status !== 404) throw new Error("Network error");
      setConnectionState(latency < 500 ? "good" : "poor");
    } catch {
      setConnectionState("offline");
    }
  }, []);

  const runAllChecks = useCallback(async () => {
    setHasRun(true);
    await checkConnection();

    const micPassed = await checkMicrophone();
    await checkCamera();
    const speakerPassed = await checkSpeaker();
    const browserPassed = await checkBrowser();

    try {
      const result = await deviceCheckMutation.mutateAsync({
        microphone: micPassed,
        camera: false,
        speaker: speakerPassed,
        browser: browserPassed,
      });
      onChecksComplete?.(result.all_passed);
    } catch {
      onChecksComplete?.(micPassed && speakerPassed && browserPassed);
    }
  }, [
    checkConnection,
    checkMicrophone,
    checkCamera,
    checkSpeaker,
    checkBrowser,
    deviceCheckMutation,
    onChecksComplete,
  ]);

  // Auto-run on mount
  useEffect(() => {
    if (!hasRun) {
      runAllChecks();
    }
  }, [hasRun, runAllChecks]);

  const allRequiredPassed = items
    .filter((item) => item.key !== "camera")
    .every((item) => item.state === "passed");

  return (
    <div className={cn("space-y-6", className)}>
      <div>
        <h3 className="text-lg font-semibold">Device Compatibility Check</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          We&apos;ll verify your device is ready for the interview. Microphone and speaker are
          required; camera is optional.
        </p>
      </div>

      {/* Check Items */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <CheckCard key={item.key} item={item} />
        ))}
      </div>

      {/* Connection Status */}
      <div className="flex items-center gap-4 rounded-lg border border-border bg-card p-4">
        <Wifi
          className={cn(
            "h-6 w-6",
            connectionState === "good" && "text-success",
            connectionState === "poor" && "text-warning",
            connectionState === "offline" && "text-destructive",
            connectionState === "checking" && "text-info",
          )}
        />
        <div className="flex-1">
          <p className="text-sm font-medium">Connection Status</p>
          <p className="text-xs text-muted-foreground">
            {connectionState === "good" && "Connection looks good"}
            {connectionState === "poor" &&
              "Connection quality is poor — some features may not work smoothly"}
            {connectionState === "offline" &&
              "Unable to reach our servers — please check your network"}
            {connectionState === "checking" && "Checking connection..."}
          </p>
        </div>
        {connectionState === "checking" && <Loader2 className="h-4 w-4 animate-spin text-info" />}
      </div>

      {/* Summary & Retry */}
      {hasRun && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            "flex items-center gap-3 rounded-lg p-4",
            allRequiredPassed
              ? "bg-success-bg text-success-foreground"
              : "bg-warning-bg text-warning-foreground",
          )}
        >
          {allRequiredPassed ? (
            <CheckCircle2 className="h-5 w-5 text-success" />
          ) : (
            <AlertCircle className="h-5 w-5 text-warning" />
          )}
          <p className="flex-1 text-sm font-medium">
            {allRequiredPassed
              ? "All required checks passed! You're ready to proceed."
              : "Some required checks failed. Please retry or adjust your device settings."}
          </p>
          {!allRequiredPassed && (
            <Button type="button" variant="outline" size="sm" onClick={runAllChecks}>
              <RotateCcw className="h-4 w-4" /> Retry
            </Button>
          )}
        </motion.div>
      )}
    </div>
  );
});

const CheckCard = memo(function CheckCard({ item }: { item: CheckItem }) {
  const { icon: Icon } = item;
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border-2 p-4 transition-all",
        item.state === "passed" && "border-success-border bg-success-bg/30",
        item.state === "failed" && "border-destructive/30 bg-destructive/5",
        item.state === "checking" && "border-info-border bg-info-bg/30",
        item.state === "pending" && "border-border bg-card",
      )}
    >
      <Icon
        className={cn(
          "mt-0.5 h-5 w-5 shrink-0",
          item.state === "passed" && "text-success",
          item.state === "failed" && "text-destructive",
          item.state === "checking" && "text-info",
          item.state === "pending" && "text-muted-foreground",
        )}
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">{item.label}</p>
        <p className="text-xs text-muted-foreground">{item.description}</p>
        {item.detail && (
          <p
            className={cn(
              "mt-1 text-xs",
              item.state === "failed" ? "text-destructive" : "text-muted-foreground",
            )}
          >
            {item.detail}
          </p>
        )}
      </div>
      {item.state === "checking" && <Loader2 className="h-4 w-4 animate-spin text-info" />}
      {item.state === "passed" && <CheckCircle2 className="h-4 w-4 text-success" />}
      {item.state === "failed" && <XCircle className="h-4 w-4 text-destructive" />}
    </div>
  );
});
