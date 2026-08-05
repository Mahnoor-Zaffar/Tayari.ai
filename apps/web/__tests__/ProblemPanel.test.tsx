import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ProblemPanel } from "@/features/coding/components/ProblemPanel";

describe("ProblemPanel", () => {
  it("renders the real default problem", () => {
    render(<ProblemPanel />);
    expect(screen.getByText("Two Sum")).toBeInTheDocument();
    expect(screen.getByText("Constraints")).toBeInTheDocument();
  });

  it("renders provided problem content", () => {
    render(
      <ProblemPanel
        title="Reverse a String"
        difficulty="easy"
        description="Reverse the given string."
        examples={[{ input: "abc", output: "cba" }]}
      />,
    );
    expect(screen.getByText("Reverse a String")).toBeInTheDocument();
    expect(screen.getByText("cba")).toBeInTheDocument();
  });
});
