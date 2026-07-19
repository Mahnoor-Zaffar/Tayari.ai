"use client";

import { useState, useCallback, useRef, useEffect } from "react";

interface SpeechRecognitionHook {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  isSupported: boolean;
  error: string | null;
  start: () => void;
  stop: () => void;
  toggle: () => void;
  onSilence?: (text: string) => void;
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

const SILENCE_MS = 1500;

export function useSpeechRecognition(): SpeechRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const finalBufferRef = useRef<string[]>([]);
  const lastTranscriptRef = useRef("");
  const isSupported = typeof window !== "undefined" &&
    (!!window.SpeechRecognition || !!window.webkitSpeechRecognition);

  const RecognitionClass = typeof window !== "undefined"
    ? (window.SpeechRecognition || window.webkitSpeechRecognition)
    : null;

  const clearSilence = useCallback(() => {
    if (silenceRef.current) {
      clearTimeout(silenceRef.current);
      silenceRef.current = null;
    }
  }, []);

  const createRecognition = useCallback(() => {
    if (!RecognitionClass) return null;
    const r = new RecognitionClass();
    r.continuous = false;
    r.interimResults = true;
    r.lang = "en-US";
    return r;
  }, [RecognitionClass]);

  const startRecognition = useCallback(() => {
    const r = createRecognition();
    if (!r) return;

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

      clearSilence();
      silenceRef.current = setTimeout(() => {
        r.stop();
      }, SILENCE_MS);
    };

    r.onerror = () => {};
    r.onend = () => {
      clearSilence();
      const buf = finalBufferRef.current;
      if (buf.length > 0) {
        const text = buf.join(" ");
        setTranscript(text);
        lastTranscriptRef.current = text;
      }
      // If we were manually stopped (isListening false), don't restart
      setIsListening((prev) => {
        if (!prev) return false;
        // Auto-restart for continuous listening
        startRecognition();
        return true;
      });
    };

    r.start();
    recognitionRef.current = r;
  }, [createRecognition, clearSilence]);

  const start = useCallback(() => {
    setError(null);
    finalBufferRef.current = [];
    setTranscript("");
    setInterimTranscript("");
    setIsListening(true);
    startRecognition();
  }, [startRecognition]);

  const stop = useCallback(() => {
    clearSilence();
    setIsListening(false);
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch { /* ignore */ }
      recognitionRef.current = null;
    }
  }, [clearSilence]);

  const toggle = useCallback(() => {
    if (isListening) stop();
    else start();
  }, [isListening, start, stop]);

  useEffect(() => {
    return () => {
      clearSilence();
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch { /* ignore */ }
      }
    };
  }, [clearSilence]);

  return {
    isListening,
    transcript,
    interimTranscript,
    isSupported,
    error,
    start,
    stop,
    toggle,
  };
}
