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
        problem={{
          id: "p1",
          slug: "reverse-string",
          title: "Reverse a String",
          difficulty: "easy",
          description: "Reverse the given string.",
          examples: [{ input: "abc", output: "cba" }],
          constraints: [],
          test_cases: [],
          total_test_count: 0,
          hidden_test_count: 0,
        }}
      />,
    );
    expect(screen.getByText("Reverse a String")).toBeInTheDocument();
    expect(screen.getByText("cba")).toBeInTheDocument();
  });

  it("shows hidden test count", () => {
    render(
      <ProblemPanel
        problem={{
          id: "p1",
          slug: "reverse-string",
          title: "Reverse a String",
          difficulty: "easy",
          description: "Reverse the given string.",
          examples: [],
          constraints: [],
          test_cases: [{ id: "v1", input: "abc", expected_output: "cba" }],
          total_test_count: 4,
          hidden_test_count: 3,
        }}
      />,
    );
    expect(screen.getByText(/3 hidden case/)).toBeInTheDocument();
  });
});
