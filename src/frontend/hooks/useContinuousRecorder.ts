'use client';

import { useRef, useState, useCallback, useEffect } from 'react';

const SPEECH_THRESHOLD = 6;
const SILENCE_TIMEOUT_MS = 5000;
const NOISE_FLOOR_DECAY = 0.995;

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

function releaseTracks(stream: MediaStream | null) {
  if (!stream) return;
  stream.getTracks().forEach((t) => {
    t.stop();
    t.enabled = false;
  });
}

export interface UseContinuousRecorderReturn {
  isListening: boolean;
  stream: MediaStream | null;
  start: (onChunkReady: (blob: Blob) => Promise<void>) => Promise<void>;
  /** Call after the AI response finishes to restart recording. */
  resume: () => void;
  stop: () => void;
}

export function useContinuousRecorder(): UseContinuousRecorderReturn {
  const [isListening, setIsListening] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array<ArrayBuffer> | null>(null);
  const rafRef = useRef(0);
  const onChunkReadyRef = useRef<((blob: Blob) => Promise<void>) | null>(null);
  const processingRef = useRef(false);
  const activeRef = useRef(false);

  // ------------------------------------------------------------------
  // Internal: restart MediaRecorder (same stream, fresh chunks)
  // ------------------------------------------------------------------
  function restartRecorder() {
    const s = streamRef.current;
    if (!s) return;

    const mimeType = resolveMimeType();
    let r: MediaRecorder;
    try {
      r = new MediaRecorder(s, mimeType ? { mimeType } : undefined);
    } catch {
      r = new MediaRecorder(s);
    }

    chunksRef.current = [];
    r.ondataavailable = (e: BlobEvent) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    r.start();
    recorderRef.current = r;
  }

  // ------------------------------------------------------------------
  // VAD polling loop — speech-first state machine
  // ------------------------------------------------------------------
  // States: SILENT → SPEAKING → WAITING → (fire chunk) → SILENT
  //   SILENT:   waiting for speech, no recording timer
  //   SPEAKING: user has spoken, silence timer may be running
  //   WAITING:  silence timer fired, chunk being sent
  // ------------------------------------------------------------------

  function startVAD() {
    let noiseFloor = 20;
    let speechActive = false;
    let silenceTimerRunning = false;
    let silenceStart = 0;

    function poll(now: number) {
      if (!activeRef.current) return;
      const a = analyserRef.current;
      const d = dataArrayRef.current;
      if (!a || !d) return;

      a.getByteTimeDomainData(d);
      const sum = d.reduce((acc, v) => acc + Math.abs(v - 128), 0);
      const rms = sum / d.length;

      const isSpeech = rms >= noiseFloor + SPEECH_THRESHOLD;

      // Only adapt noise floor during non-speech frames
      if (!isSpeech) {
        if (rms < noiseFloor) noiseFloor = rms;
        else noiseFloor = noiseFloor * NOISE_FLOOR_DECAY + rms * (1 - NOISE_FLOOR_DECAY);
      }

      if (isSpeech) {
        if (!speechActive) {
          speechActive = true;
        }
        silenceTimerRunning = false;
        silenceStart = 0;
      } else if (speechActive && !processingRef.current) {
        if (silenceStart === 0) {
          silenceStart = now;
        } else if (!silenceTimerRunning && now - silenceStart >= SILENCE_TIMEOUT_MS) {
          silenceTimerRunning = true;

          processingRef.current = true;
          const rec = recorderRef.current;
          if (rec && rec.state === 'recording') {
            rec.onstop = () => {
              const mime = rec.mimeType || 'audio/webm';
              const blob = new Blob(chunksRef.current, { type: mime });
              chunksRef.current = [];

              const cb = onChunkReadyRef.current;
              if (cb) {
                cb(blob)
                  .then(() => {})
                  .catch(() => {
                    processingRef.current = false;
                  });
              } else {
                processingRef.current = false;
              }
            };
            rec.stop();
          } else {
            processingRef.current = false;
          }

          speechActive = false;
          silenceStart = 0;
        }
      }

      rafRef.current = requestAnimationFrame(poll);
    }

    rafRef.current = requestAnimationFrame(poll);
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  const start = useCallback(
    async (onChunkReady: (blob: Blob) => Promise<void>) => {
      if (activeRef.current) return;
      activeRef.current = true;
      onChunkReadyRef.current = onChunkReady;

      try {
        const micStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: { ideal: 1 },
            sampleRate: { ideal: 16000 },
            echoCancellation: { ideal: true },
            noiseSuppression: { ideal: true },
          },
        });

        streamRef.current = micStream;
        setStream(micStream);

        restartRecorder();

        const audioCtx = new AudioContext();
        if (audioCtx.state === 'suspended') {
          await audioCtx.resume();
        }
        const source = audioCtx.createMediaStreamSource(micStream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);

        audioCtxRef.current = audioCtx;
        analyserRef.current = analyser;
        dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);

        setIsListening(true);
        startVAD();
      } catch (err) {
        activeRef.current = false;
        releaseTracks(streamRef.current);
        streamRef.current = null;
        throw err;
      }
    },
    [],
  );

  const stop = useCallback(() => {
    activeRef.current = false;
    cancelAnimationFrame(rafRef.current);

    const rec = recorderRef.current;
    if (rec && rec.state !== 'inactive') {
      rec.ondataavailable = null;
      rec.onstop = null;
      try {
        rec.stop();
      } catch {
        /* already inactive */
      }
    }
    recorderRef.current = null;
    chunksRef.current = [];

    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }

    releaseTracks(streamRef.current);
    streamRef.current = null;
    processingRef.current = false;
    setStream(null);
    setIsListening(false);
  }, []);

  const resume = useCallback(() => {
    if (!activeRef.current) return;
    if (streamRef.current) {
      restartRecorder();
    }
    processingRef.current = false;
  }, []);

  useEffect(() => stop, [stop]);

  return { isListening, stream, start, resume, stop };
}
