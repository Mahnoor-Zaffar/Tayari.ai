import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useEffect } from "react";

import { useFocusTrap } from "@/hooks/use-focus-trap";

function TestComponent({ open }: { open: boolean }) {
  const ref = useFocusTrap(open);

  return (
    <div ref={ref} data-testid="container">
      <button type="button" data-testid="first">
        First
      </button>
      <button type="button" data-testid="middle">
        Middle
      </button>
      <button type="button" data-testid="last">
        Last
      </button>
      <a href="#" data-testid="link">
        Link
      </a>
    </div>
  );
}

describe("useFocusTrap", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("focuses first focusable element when opened", () => {
    const { rerender } = render(<TestComponent open={false} />);
    expect(document.activeElement).not.toBe(screen.getByTestId("first"));

    rerender(<TestComponent open={true} />);
    expect(document.activeElement).toBe(screen.getByTestId("first"));
  });

  it("traps tab focus within container", () => {
    render(<TestComponent open={true} />);
    const first = screen.getByTestId("first");
    const last = screen.getByTestId("last");

    first.focus();
    expect(document.activeElement).toBe(first);

    // Tab backwards from first should wrap to last
    fireEvent.keyDown(first, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(last);
  });
});
