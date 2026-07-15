"use client";

import { useState, useCallback } from "react";

const NOTES_STORAGE_KEY_PREFIX = "interview-notes-";

export function useNotes(interviewId: string) {
  const [notes, setNotesState] = useState<string>(() => {
    if (typeof window === "undefined") return "";
    try {
      return localStorage.getItem(`${NOTES_STORAGE_KEY_PREFIX}${interviewId}`) ?? "";
    } catch {
      return "";
    }
  });

  const setNotes = useCallback(
    (text: string) => {
      setNotesState(text);
      try {
        localStorage.setItem(`${NOTES_STORAGE_KEY_PREFIX}${interviewId}`, text);
      } catch {
        // localStorage may be full
      }
    },
    [interviewId],
  );

  const clearNotes = useCallback(() => {
    setNotesState("");
    try {
      localStorage.removeItem(`${NOTES_STORAGE_KEY_PREFIX}${interviewId}`);
    } catch {
      // ignore
    }
  }, [interviewId]);

  return { notes, setNotes, clearNotes };
}
