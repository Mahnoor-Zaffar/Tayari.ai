import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { InterviewProgress } from "@/features/dashboard/components/InterviewProgress";
import type { LatestReport } from "@/features/dashboard/types";

describe("InterviewProgress", () => {
  it("renders loading skeleton", () => {
    const { container } = render(<InterviewProgress isLoading completed={0} total={0} />);
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders empty state when no interviews", () => {
    render(<InterviewProgress isLoading={false} completed={0} total={0} />);
    expect(screen.getByText("No interviews yet")).toBeInTheDocument();
  });

  it("renders progress and latest report", () => {
    const report: LatestReport = {
      interview_id: "1",
      overall_score: 88,
      hire_verdict: "hire",
      created_at: "2025-06-15T10:00:00Z",
    };
    render(<InterviewProgress isLoading={false} completed={5} total={10} latestReport={report} />);

    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("88%")).toBeInTheDocument();
    expect(screen.getByText(/Good performance/)).toBeInTheDocument();
  });
});
