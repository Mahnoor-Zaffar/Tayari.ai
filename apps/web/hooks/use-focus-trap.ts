"use client";

import { useEffect, useRef, type RefObject } from "react";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE));
}

export function useFocusTrap(open: boolean): RefObject<HTMLDivElement | null> {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;

    const container = ref.current;
    if (!container) return;

    const previouslyFocused = document.activeElement as HTMLElement | null;

    const focusables = getFocusableElements(container);
    if (focusables.length > 0) {
      focusables[0]?.focus();
    }

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== "Tab") return;
      const elements = getFocusableElements(container!);
      if (elements.length === 0) return;

      const first = elements[0]!;
      const last = elements[elements.length - 1]!;

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [open]);

  return ref;
}
