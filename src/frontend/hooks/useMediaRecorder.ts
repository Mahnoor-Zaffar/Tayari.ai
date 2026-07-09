'use client';

import { useRef, useState, useCallback, useEffect } from 'react';

/** Detects Safari/iOS WebKit — used for MIME-type fallback. */
function isWebKit(): boolean {
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent.toLowerCase();
  return ua.includes('safari') && !ua.includes('chrome');
}

/**
 * Resolves the best supported MIME type for the current browser.
 *   - Chrome/Firefox: audio/webm;codecs=opus
 *   - Safari/iOS:      audio/ogg;codecs=opus  (webm not supported)
 */
function resolveMimeType(): string {
  const preferred = isWebKit()
    ? 'audio/ogg;codecs=opus'
    : 'audio/webm;codecs=opus';

  if (MediaRecorder.isTypeSupported(preferred)) return preferred;

  // Last-resort fallback — browser picks the default.
  const fallback = isWebKit() ? 'audio/ogg' : 'audio/webm';
  if (MediaRecorder.isTypeSupported(fallback)) return fallback;

  return '';
}

// ---------------------------------------------------------------------------
// Hook return type (consumed by InterviewView, MicButton, etc.)
// ---------------------------------------------------------------------------
export interface UseMediaRecorderReturn {
  /** `true` while the microphone is actively recording. */
  isRecording: boolean;
  /** The most recently completed recording blob, or `null` if none. */
  audioBlob: Blob | null;
  /** Human-readable error string, or `null` when no error is present. */
  error: string | null;
  /** The active `MediaStream` while recording, otherwise `null`. */
  stream: MediaStream | null;

  /** Requests mic access, configures the recorder, and begins capture. */
  startRecording: () => Promise<void>;
  /** Stops the recorder, finalises the blob, releases the mic stream. */
  stopRecording: () => Promise<Blob>;
  /** Releases all hardware resources immediately (call in `useEffect` cleanup). */
  release: () => void;
}

/**
 * `useMediaRecorder` — turn-based audio capture hook.
 *
 * Manages the full lifecycle of browser audio recording:
 *   - Requests mic access with transcription-optimised constraints (mono, 16 kHz,
 *     echo cancellation).
 *   - Selects the best codec wrapper for the current browser (WebM for Chrome,
 *     Ogg for Safari).
 *   - Exposes `startRecording` / `stopRecording` for turn-based capture.
 *   - Automatically releases the hardware stream on unmount.
 *
 * @returns {UseMediaRecorderReturn}  Recording state, handlers, and stream ref.
 */
export function useMediaRecorder(): UseMediaRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  // Mutable refs — never trigger re-renders.
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // -----------------------------------------------------------------------
  // Internal: release all hardware resources
  // -----------------------------------------------------------------------

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
    // Guard against concurrent starts.
    if (mediaRecorderRef.current?.state === 'recording') return;

    setError(null);
    setAudioBlob(null);

    let micStream: MediaStream;

    try {
      micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: { ideal: 1 },
          sampleRate: { ideal: 16000 },
          echoCancellation: { ideal: true },
          noiseSuppression: { ideal: true },
        },
      });
    } catch (err) {
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

    // Keep a ref for cleanup.
    streamRef.current = micStream;

    const mimeType = resolveMimeType();

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(micStream, mimeType ? { mimeType } : undefined);
    } catch {
      // If the constructor throws (bad mime), let the browser pick.
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

        // Release the hardware stream.
        releaseStream(streamRef.current);
        streamRef.current = null;
        mediaRecorderRef.current = null;
        chunksRef.current = [];

        resolve(blob);
      };

      // Edge-case: if `stop()` is called before any data fires, force a
      // final blob with the current buffer.
      if (recorder.state !== 'inactive') {
        recorder.requestData?.();
        recorder.stop();
      }
    });
  }, []);

  // -----------------------------------------------------------------------
  // release  (imperative cleanup — call in useEffect return)
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
    resetState();
  }, []);

  // -----------------------------------------------------------------------
  // Automatic cleanup on unmount
  // -----------------------------------------------------------------------

  useEffect(() => release, [release]);

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  return {
    isRecording,
    audioBlob,
    error,
    stream,
    startRecording,
    stopRecording,
    release,
  };
}
