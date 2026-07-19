"use client";

import { useState, useCallback, useRef, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const WS_BASE = API_BASE.replace(/^http/, "ws");

interface StreamingRecognitionHook {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  isSupported: boolean;
  error: string | null;
  latencyMs: number;
  source: "funasr";
  start: () => void;
  stop: () => void;
  toggle: () => void;
}

export function useStreamingRecognition(
  accessToken?: string | null,
  language: string = "en",
): StreamingRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const tokenRef = useRef<string | null>(null);
  const bufferRef = useRef<string[]>([]);
  const startTimeRef = useRef(0);

  tokenRef.current = accessToken ?? null;

  // Check browser support
  const isSupported =
    typeof window !== "undefined" &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof AudioContext !== "undefined";

  // Connect streaming WebSocket
  const connectStream = useCallback((): Promise<WebSocket> => {
    return new Promise((resolve, reject) => {
      const wsUrl = `${WS_BASE}/voice/stream`;
      const ws = new WebSocket(wsUrl);

      ws.binaryType = "arraybuffer";

      ws.onopen = () => {
        // Send start config
        ws.send(JSON.stringify({ type: "start", language }));
        wsRef.current = ws;
        resolve(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "partial") {
            setInterimTranscript(data.text);
          } else if (data.type === "final") {
            if (data.text?.trim()) {
              bufferRef.current.push(data.text.trim());
              setTranscript(bufferRef.current.join(" "));
              setLatencyMs(Date.now() - startTimeRef.current);
            }
            setInterimTranscript("");
          } else if (data.type === "error") {
            console.error("Stream error:", data.message);
            setError(data.message);
          }
        } catch {
          // Ignore parse errors
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        reject(new Error("WebSocket connection failed"));
      };

      ws.onclose = () => {
        wsRef.current = null;
      };
    });
  }, [language]);

  // Start microphone + streaming
  const start = useCallback(async () => {
    if (!isSupported) {
      setError("Audio not supported in this browser");
      return;
    }

    setError(null);
    bufferRef.current = [];
    setTranscript("");
    setInterimTranscript("");
    startTimeRef.current = Date.now();

    try {
      // 1. Get microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100, // Let browser pick, we resample in worklet
        },
      });
      streamRef.current = stream;

      // 2. Connect WebSocket
      const ws = await connectStream();

      // 3. Set up AudioContext + worklet
      const audioContext = new AudioContext({ sampleRate: 44100 });
      if (audioContext.state === "suspended") {
        await audioContext.resume();
      }
      audioContextRef.current = audioContext;

      // Load AudioWorklet processor
      await audioContext.audioWorklet.addModule("/audio-processor.js");
      const workletNode = new AudioWorkletNode(audioContext, "pcm-processor");
      workletNodeRef.current = workletNode;

      // When worklet sends PCM chunks, send to WebSocket
      workletNode.port.onmessage = (event) => {
        const pcmData = event.data as Int16Array;
        if (ws.readyState === WebSocket.OPEN) {
          startTimeRef.current = Date.now();
          ws.send(pcmData.buffer);
        }
      };

      // Connect mic → worklet → destination (needed to keep node alive)
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(workletNode);
      workletNode.connect(audioContext.destination);

      setIsListening(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to start recording";
      setError(msg);
      console.error("Start error:", err);
    }
  }, [isSupported, connectStream]);

  // Stop recording
  const stop = useCallback(async () => {
    setIsListening(false);

    // Close worklet
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      await audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop media tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "stop" }));
        wsRef.current.close();
      }
      wsRef.current = null;
    }
  }, []);

  const toggle = useCallback(() => {
    if (isListening) stop();
    else start();
  }, [isListening, start, stop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (workletNodeRef.current) workletNodeRef.current.disconnect();
      if (audioContextRef.current) audioContextRef.current.close();
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    isSupported,
    error,
    latencyMs,
    source: "funasr",
    start,
    stop,
    toggle,
  };
}
