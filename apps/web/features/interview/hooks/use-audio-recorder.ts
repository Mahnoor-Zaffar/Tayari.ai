"use client";

import { useState, useCallback, useRef, useEffect } from "react";

const MIME_TYPES = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];

function getSupportedMimeType(): string | null {
  if (typeof MediaRecorder === "undefined") return null;
  for (const type of MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return null;
}

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const mimeTypeRef = useRef<string | null>(null);

  const mimeType = typeof window !== "undefined" ? getSupportedMimeType() : null;
  const isSupported =
    !!mimeType && typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia;

  useEffect(() => {
    mimeTypeRef.current = mimeType;
  }, [mimeType]);

  const monitorLevel = useCallback(() => {
    if (!analyserRef.current) return;
    const data = new Uint8Array(analyserRef.current.fftSize);
    analyserRef.current.getByteTimeDomainData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      const v = data[i];
      if (v == null) continue;
      const val = (v - 128) / 128;
      sum += val * val;
    }
    const rms = Math.sqrt(sum / data.length);
    setAudioLevel(Math.min(1, rms * 3));
    animFrameRef.current = requestAnimationFrame(monitorLevel);
  }, []);

  const start = useCallback(async () => {
    const mt = mimeTypeRef.current;
    if (!mt || !navigator.mediaDevices?.getUserMedia) return;
    if (recorderRef.current?.state === "recording") return;

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 16000,
      },
    });

    streamRef.current = stream;

    // Set up audio level monitoring (once)
    if (!audioCtxRef.current) {
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      audioCtxRef.current = audioCtx;
    }
    monitorLevel();

    const recorder = new MediaRecorder(stream, { mimeType: mt });
    recorderRef.current = recorder;
    recorder.start();
    setIsRecording(true);
  }, [monitorLevel]);

  const stop = useCallback(async (): Promise<Blob | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") return null;

    return new Promise<Blob | null>((resolve) => {
      const chunks: Blob[] = [];
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) chunks.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: mimeTypeRef.current || "audio/webm" });
        recorderRef.current = null;
        setIsRecording(false);
        resolve(blob.size > 0 ? blob : null);
      };
      recorder.stop();
    });
  }, []);

  /** Stop current recording, return the blob, and immediately restart. */
  const flushChunk = useCallback(async (): Promise<Blob | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording") return null;

    return new Promise<Blob | null>((resolve) => {
      const chunks: Blob[] = [];
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) chunks.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: mimeTypeRef.current || "audio/webm" });

        // Restart immediately
        if (streamRef.current?.active && mimeTypeRef.current) {
          try {
            const newRecorder = new MediaRecorder(streamRef.current, {
              mimeType: mimeTypeRef.current,
            });
            newRecorder.start();
            recorderRef.current = newRecorder;
          } catch {
            // Failed to restart — that's ok
          }
        }

        resolve(blob.size > 0 ? blob : null);
      };
      recorder.stop();
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
      streamRef.current?.getTracks().forEach((t) => t.stop());
      audioCtxRef.current?.close();
    };
  }, []);

  return { isRecording, isSupported, start, stop, flushChunk, audioLevel };
}
