"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useAudioRecorder } from "./use-audio-recorder";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface WhisperRecognitionHook {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  isSupported: boolean;
  error: string | null;
  source: "whisper" | "browser";
  latencyMs: number;
  start: () => void;
  stop: () => void;
  toggle: () => void;
}

const CHUNK_INTERVAL_MS = 4000;

export function useWhisperRecognition(accessToken?: string | null): WhisperRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"whisper" | "browser">("whisper");
  const [latencyMs, setLatencyMs] = useState(0);

  const recorder = useAudioRecorder();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const abortRef = useRef(false);
  const bufferRef = useRef<string[]>([]);
  const tokenRef = useRef<string | null>(null);
  const speechRecRef = useRef<any>(null);

  // Keep token ref in sync with prop
  tokenRef.current = accessToken ?? null;

  const sendChunk = useCallback(async (blob: Blob) => {
    if (blob.size < 500) return;

    const startTime = Date.now();

    try {
      const formData = new FormData();
      formData.append("file", blob, `chunk-${Date.now()}.webm`);

      const headers: Record<string, string> = {};
      if (tokenRef.current) {
        headers["Authorization"] = `Bearer ${tokenRef.current}`;
      }

      const resp = await fetch(`${API_BASE}/voice/transcribe`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (resp.ok) {
        const data = await resp.json();
        const text = data?.data?.text ?? "";
        if (text.trim()) {
          bufferRef.current.push(text.trim());
          setTranscript(bufferRef.current.join(" "));
          setLatencyMs(Date.now() - startTime);
        }
      } else {
        console.warn("Transcription failed:", resp.status);
      }
    } catch (err) {
      console.warn("Transcription error:", err);
    }
  }, []);

  const startWhisper = useCallback(async (): Promise<boolean> => {
    try {
      await recorder.start();
      setSource("whisper");

      // Periodically flush chunks and send to Whisper
      intervalRef.current = setInterval(async () => {
        if (abortRef.current) return;
        const chunk = await recorder.flushChunk();
        if (chunk) await sendChunk(chunk);
      }, CHUNK_INTERVAL_MS);

      return true;
    } catch (err) {
      console.warn("Whisper failed:", err);
      return false;
    }
  }, [recorder, sendChunk]);

  const startBrowserFallback = useCallback((): boolean => {
    const SR =
      typeof window !== "undefined"
        ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
        : null;
    if (!SR) return false;

    const r = new SR();
    r.continuous = true;
    r.interimResults = true;
    r.lang = "en-US";

    r.onresult = (event: any) => {
      let finalText = "";
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (!result) continue;
        const alt = result[0];
        if (!alt) continue;
        if (result.isFinal) {
          finalText += (finalText ? " " : "") + alt.transcript;
        } else {
          interimText += (interimText ? " " : "") + alt.transcript;
        }
      }
      if (finalText) {
        bufferRef.current.push(finalText);
        setTranscript(bufferRef.current.join(" "));
      }
      setInterimTranscript(interimText);
    };

    r.onerror = (event: any) => {
      if (event.error === "not-allowed") {
        setError("Microphone access denied.");
        setIsListening(false);
      }
    };

    r.onend = () => {
      if (!abortRef.current) {
        try {
          r.start();
        } catch {
          /* ignore */
        }
      }
    };

    try {
      r.start();
      speechRecRef.current = r;
      setSource("browser");
      return true;
    } catch {
      return false;
    }
  }, []);

  const start = useCallback(async () => {
    setError(null);
    abortRef.current = false;
    bufferRef.current = [];
    setTranscript("");
    setInterimTranscript("");

    setIsListening(true);

    const whisperOk = await startWhisper();
    if (!whisperOk) {
      const browserOk = startBrowserFallback();
      if (!browserOk) {
        setError("Speech recognition not available in this browser.");
        setIsListening(false);
      }
    }
  }, [startWhisper, startBrowserFallback]);

  const stop = useCallback(async () => {
    abortRef.current = true;

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Flush final chunk from Whisper
    if (recorder.isRecording) {
      const chunk = await recorder.flushChunk();
      if (chunk) await sendChunk(chunk);
      await recorder.stop();
    }

    // Stop browser fallback
    if (speechRecRef.current) {
      try {
        speechRecRef.current.stop();
      } catch {
        /* ignore */
      }
      speechRecRef.current = null;
    }

    setIsListening(false);
  }, [recorder, sendChunk]);

  const toggle = useCallback(() => {
    if (isListening) stop();
    else start();
  }, [isListening, start, stop]);

  // Cleanup on unmount only — must NOT depend on `recorder` (new object every render)
  useEffect(() => {
    return () => {
      abortRef.current = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (speechRecRef.current) {
        try {
          speechRecRef.current.abort();
        } catch {
          /* ignore */
        }
      }
    };
  }, []);

  const browserSupported =
    (typeof window !== "undefined" && !!(window as any).SpeechRecognition) ||
    !!(window as any).webkitSpeechRecognition;

  return {
    isListening,
    transcript,
    interimTranscript,
    isSupported: recorder.isSupported || browserSupported,
    error,
    source,
    latencyMs,
    start,
    stop,
    toggle,
  };
}
