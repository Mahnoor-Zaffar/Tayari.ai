"use client";

import { useState, useCallback, useRef, useEffect, useMemo } from "react";

interface SpeechRecognitionHook {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  isSupported: boolean;
  error: string | null;
  source: "whisper" | "browser";
  start: () => void;
  stop: () => void;
  toggle: () => void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

const SILENCE_MS = 5000;
const RESTART_DELAY_MS = 300;

export function useSpeechRecognition(): SpeechRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const restartRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const finalBufferRef = useRef<string[]>([]);
  const lastTranscriptRef = useRef("");
  const shouldRestartRef = useRef(false);
  const manualStopRef = useRef(false);

  const RecognitionClass = useMemo(() => {
    if (typeof window === "undefined") return null;
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }, []);

  useEffect(() => {
    setIsSupported(!!RecognitionClass);
  }, [RecognitionClass]);

  const clearTimers = useCallback(() => {
    if (silenceRef.current) {
      clearTimeout(silenceRef.current);
      silenceRef.current = null;
    }
    if (restartRef.current) {
      clearTimeout(restartRef.current);
      restartRef.current = null;
    }
  }, []);

  const scheduleRestart = useCallback(() => {
    if (!shouldRestartRef.current || manualStopRef.current) return;
    restartRef.current = setTimeout(() => {
      if (shouldRestartRef.current && !manualStopRef.current) {
        startRecognition();
      }
    }, RESTART_DELAY_MS);
  }, []);

  function startRecognition() {
    if (!RecognitionClass) return;
    try {
      const r = new RecognitionClass();
      r.continuous = true;
      r.interimResults = true;
      r.lang = "en-US";

      r.onresult = (event: SpeechRecognitionEvent) => {
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
          finalBufferRef.current.push(finalText);
          const all = finalBufferRef.current.join(" ");
          setTranscript(all);
          lastTranscriptRef.current = all;
        }
        setInterimTranscript(interimText);
      };

      r.onerror = (event: SpeechRecognitionErrorEvent) => {
        const errType = event.error;
        if (errType === "not-allowed") {
          setError("Microphone access denied. Please allow mic access in your browser settings.");
          shouldRestartRef.current = false;
          setIsListening(false);
        } else if (errType === "no-speech") {
          // Silence — onend will handle restart
        } else if (errType === "network") {
          setError("Speech recognition network error.");
        } else if (errType !== "aborted") {
          setError(`Speech error: ${errType}`);
        }
      };

      r.onend = () => {
        clearTimers();
        const buf = finalBufferRef.current;
        if (buf.length > 0) {
          const text = buf.join(" ");
          setTranscript(text);
          lastTranscriptRef.current = text;
        }
        scheduleRestart();
      };

      r.start();
      recognitionRef.current = r;
    } catch {
      // Already started or other error
    }
  }

  const start = useCallback(() => {
    setError(null);
    finalBufferRef.current = [];
    lastTranscriptRef.current = "";
    setTranscript("");
    setInterimTranscript("");
    manualStopRef.current = false;
    shouldRestartRef.current = true;
    setIsListening(true);
    startRecognition();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [RecognitionClass, clearTimers]);

  const stop = useCallback(() => {
    clearTimers();
    manualStopRef.current = true;
    shouldRestartRef.current = false;
    setIsListening(false);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        /* ignore */
      }
      recognitionRef.current = null;
    }
  }, [clearTimers]);

  const toggle = useCallback(() => {
    if (isListening) stop();
    else start();
  }, [isListening, start, stop]);

  useEffect(() => {
    return () => {
      clearTimers();
      shouldRestartRef.current = false;
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          /* ignore */
        }
        recognitionRef.current = null;
      }
    };
  }, [clearTimers]);

  return {
    isListening,
    transcript,
    interimTranscript,
    isSupported,
    error,
    source: "browser",
    start,
    stop,
    toggle,
  };
}
