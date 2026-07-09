'use client';

import { useRef, useState, useCallback, useEffect, useMemo } from 'react';

// ---------------------------------------------------------------------------
// Browser detection & MIME-type resolution
// ---------------------------------------------------------------------------

function isWebKit(): boolean {
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent.toLowerCase();
  return ua.includes('safari') && !ua.includes('chrome');
}

function resolveMimeType(): string {
  const preferred = isWebKit()
    ? 'audio/ogg;codecs=opus'
    : 'audio/webm;codecs=opus';
  if (MediaRecorder.isTypeSupported(preferred)) return preferred;
  const fallback = isWebKit() ? 'audio/ogg' : 'audio/webm';
  if (MediaRecorder.isTypeSupported(fallback)) return fallback;
  return '';
}

// ---------------------------------------------------------------------------
// Hook return type
// ---------------------------------------------------------------------------

export interface UseMediaRecorderReturn {
  isRecording: boolean;
  audioBlob: Blob | null;
  error: string | null;
  stream: MediaStream | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob>;
  release: () => void;
}

/**
 * `useMediaRecorder` — turn-based audio capture hook.
 *
 * Optimisations for transcription accuracy:
 *  - Sample rate: prefers 48 kHz, falls back to 16 kHz
 *  - Channel layout: mono (1 channel) — multi-channel can cause phase
 *    cancellation in downstream speech engines
 *  - Echo cancellation, noise suppression, and automatic gain control
 *    enabled to isolate the speaker's voice from ambient noise
 */
export function useMediaRecorder(): UseMediaRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const startingRef = useRef(false);

  function releaseStream(streamToRelease: MediaStream | null) {
    if (!streamToRelease) return;
    streamToRelease.getTracks().forEach((track) => {
      track.stop();
      track.enabled = false;
    });
  }

  function resetState() {
    setIsRecording(false);
    setStream(null);
    setAudioBlob(null);
    mediaRecorderRef.current = null;
    chunksRef.current = [];
  }

  // -----------------------------------------------------------------------
  // startRecording
  // -----------------------------------------------------------------------

  const startRecording = useCallback(async (): Promise<void> => {
    if (mediaRecorderRef.current?.state === 'recording') return;
    if (startingRef.current) return;
    startingRef.current = true;

    setError(null);
    setAudioBlob(null);

    let micStream: MediaStream;

    try {
      micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: { ideal: 48000 },
          channelCount: { ideal: 1 },
          echoCancellation: { ideal: true },
          noiseSuppression: { ideal: true },
          autoGainControl: { ideal: true },
        },
      });
    } catch (err) {
      startingRef.current = false;
      let message: string;
      if (err instanceof DOMException) {
        switch (err.name) {
          case 'NotAllowedError':
            message = 'Microphone permission denied. Allow access in your browser settings.';
            break;
          case 'NotFoundError':
            message = 'No microphone found. Connect a microphone and try again.';
            break;
          case 'NotReadableError':
            message = 'Microphone is busy (used by another app). Close it and try again.';
            break;
          default:
            message = `Microphone access failed: ${err.message}`;
        }
      } else if (err instanceof Error) {
        message = err.message;
      } else {
        message = 'An unknown error occurred while accessing the microphone.';
      }
      setError(message);
      throw err;
    }

    streamRef.current = micStream;

    const mimeType = resolveMimeType();

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(micStream, mimeType ? { mimeType } : undefined);
    } catch {
      recorder = new MediaRecorder(micStream);
    }

    chunksRef.current = [];

    recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };

    recorder.start();
    mediaRecorderRef.current = recorder;
    setStream(micStream);
    setIsRecording(true);
    startingRef.current = false;
  }, []);

  // -----------------------------------------------------------------------
  // stopRecording
  // -----------------------------------------------------------------------

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorderRef.current;

      if (!recorder || recorder.state === 'inactive') {
        reject(new Error('No active recording to stop.'));
        return;
      }

      recorder.onstop = () => {
        const mime = recorder.mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: mime });

        setAudioBlob(blob);
        setIsRecording(false);
        setStream(null);

        releaseStream(streamRef.current);
        streamRef.current = null;
        mediaRecorderRef.current = null;
        chunksRef.current = [];
        startingRef.current = false;

        resolve(blob);
      };

      recorder.stop();
    });
  }, []);

  // -----------------------------------------------------------------------
  // release — imperative cleanup for useEffect
  // -----------------------------------------------------------------------

  const release = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.ondataavailable = null;
      recorder.onstop = null;
      try { recorder.stop(); } catch { /* already inactive */ }
    }

    releaseStream(streamRef.current);
    streamRef.current = null;
    startingRef.current = false;
    resetState();
  }, []);

  useEffect(() => release, [release]);

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  return useMemo(
    () => ({
      isRecording,
      audioBlob,
      error,
      stream,
      startRecording,
      stopRecording,
      release,
    }),
    [isRecording, audioBlob, error, stream, startRecording, stopRecording, release],
  );
}
