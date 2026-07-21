"use client";

import { useState, useCallback, useRef, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const WS_BASE = API_BASE.replace(/^http/, "ws");

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_DELAY_MS = 1000;

interface DeepgramRecognitionHook {
  isListening: boolean;
  isSpeaking: boolean;
  isReconnecting: boolean;
  audioLevel: number;
  transcript: string;
  interimTranscript: string;
  autoSubmitTrigger: number;
  isSupported: boolean;
  error: string | null;
  start: () => void;
  stop: () => void;
  toggle: () => void;
}

export function useDeepgramRecognition(
  accessToken?: string | null,
  language: string = "en",
): DeepgramRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [autoSubmitTrigger, setAutoSubmitTrigger] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number>(0);
  const bufferRef = useRef<string[]>([]);
  const reconnectAttemptsRef = useRef(0);
  const shouldReconnectRef = useRef(false);
  const startRequestedRef = useRef(false);

  const isSupported =
    typeof window !== "undefined" &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof AudioContext !== "undefined";

  // ── Connect WebSocket to backend ────────────────────────────────────
  const connectWs = useCallback(
    (): Promise<WebSocket> =>
      new Promise((resolve, reject) => {
        const ws = new WebSocket(`${WS_BASE}/voice/stream`);
        ws.binaryType = "arraybuffer";

        ws.onopen = () => {
          ws.send(JSON.stringify({ type: "start", language }));
          wsRef.current = ws;
          reconnectAttemptsRef.current = 0;
          setIsReconnecting(false);
          setError(null);
          resolve(ws);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "partial") {
              setInterimTranscript(data.text);
              setIsSpeaking(true);
            } else if (data.type === "final") {
              if (data.text?.trim()) {
                bufferRef.current.push(data.text.trim());
                setTranscript(bufferRef.current.join(" "));
              }
              setInterimTranscript("");

              if (data.speech_final) {
                // End of utterance — trigger auto-submit
                setIsSpeaking(false);
                setAutoSubmitTrigger((n) => n + 1);
              }
            } else if (data.type === "error") {
              console.error("Voice stream error:", data.message);
              setError(data.message);
            }
          } catch {
            // Ignore parse errors
          }
        };

        ws.onerror = () => {
          reject(new Error("WebSocket connection failed"));
        };

        ws.onclose = () => {
          wsRef.current = null;
          setIsSpeaking(false);

          // Auto-reconnect if still in listening mode
          if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
            setIsReconnecting(true);
            const delay = RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current);
            reconnectAttemptsRef.current += 1;
            setTimeout(() => {
              if (shouldReconnectRef.current && startRequestedRef.current) {
                connectWs().catch(() => {
                  // Reconnect failed, will retry on next cycle
                });
              }
            }, delay);
          } else if (shouldReconnectRef.current) {
            // Max reconnect attempts exhausted
            setIsReconnecting(false);
            setError("Voice connection lost. Click mic to retry.");
          }
        };
      }),
    [language],
  );

  // ── Start microphone + streaming ────────────────────────────────────
  const start = useCallback(async () => {
    if (!isSupported) {
      setError("Audio not supported in this browser");
      return;
    }

    setError(null);
    setIsReconnecting(false);
    bufferRef.current = [];
    setTranscript("");
    setInterimTranscript("");
    setIsSpeaking(false);
    startRequestedRef.current = true;
    shouldReconnectRef.current = true;

    try {
      // 1. Get microphone
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      // 2. Connect WebSocket
      await connectWs();

      // 3. Set up AudioContext + worklet
      const audioContext = new AudioContext({ sampleRate: 44100 });
      if (audioContext.state === "suspended") {
        await audioContext.resume();
      }
      audioContextRef.current = audioContext;

      await audioContext.audioWorklet.addModule("/audio-processor.js");
      const workletNode = new AudioWorkletNode(audioContext, "pcm-processor");
      workletNodeRef.current = workletNode;

      // 4. Send PCM chunks to WebSocket
      workletNode.port.onmessage = (event) => {
        const pcmData = event.data as Int16Array;
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(pcmData.buffer);
        }
      };

      // 5. Wire up audio graph: mic → source → analyser → worklet → destination
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyserRef.current = analyser;

      source.connect(analyser);
      analyser.connect(workletNode);
      workletNode.connect(audioContext.destination);
      sourceRef.current = source;

      // 6. Start audio level monitoring
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i]!;
        }
        const avg = sum / dataArray.length / 255; // normalize 0–1
        setAudioLevel(avg);
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      animFrameRef.current = requestAnimationFrame(updateLevel);

      setIsListening(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to start recording";
      setError(msg);
      console.error("Voice start error:", err);
      shouldReconnectRef.current = false;
      startRequestedRef.current = false;
    }
  }, [isSupported, connectWs]);

  // ── Stop microphone + streaming ─────────────────────────────────────
  const stop = useCallback(() => {
    startRequestedRef.current = false;
    shouldReconnectRef.current = false;
    setIsListening(false);
    setIsSpeaking(false);
    setIsReconnecting(false);
    setAudioLevel(0);

    // Stop audio level monitoring
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = 0;
    }

    // Disconnect analyser
    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }

    // Disconnect worklet
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    // Disconnect source
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    // Close AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    // Stop media tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      try {
        if (wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "stop" }));
        }
        wsRef.current.close();
      } catch {
        // Ignore
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
      shouldReconnectRef.current = false;
      startRequestedRef.current = false;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (analyserRef.current) analyserRef.current.disconnect();
      if (workletNodeRef.current) workletNodeRef.current.disconnect();
      if (sourceRef.current) sourceRef.current.disconnect();
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return {
    isListening,
    isSpeaking,
    isReconnecting,
    audioLevel,
    transcript,
    interimTranscript,
    autoSubmitTrigger,
    isSupported,
    error,
    start,
    stop,
    toggle,
  };
}
