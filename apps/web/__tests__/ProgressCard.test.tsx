import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { ProgressCard } from "@/components/shared/ProgressCard";

describe("ProgressCard", () => {
  it("renders label and value", () => {
    render(<ProgressCard label="Completed" value={5} max={10} />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("5/10")).toBeInTheDocument();
  });

  it("renders progressbar with correct aria attributes", () => {
    render(<ProgressCard label="Progress" value={7} max={10} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "7");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "10");
  });

  it("handles zero max without crashing", () => {
    render(<ProgressCard label="Empty" value={0} max={0} />);
    expect(screen.getByText("0/0")).toBeInTheDocument();
  });
});
