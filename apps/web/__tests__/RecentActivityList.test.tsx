import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { RecentActivityList } from "@/features/dashboard/components/RecentActivityList";
import type { RecentInterview } from "@/features/dashboard/types";

const mockInterviews: RecentInterview[] = [
  {
    id: "1",
    type: "coding",
    company: "Google",
    status: "completed",
    overall_score: 85,
    completed_at: "2025-06-15T10:00:00Z",
    created_at: "2025-06-14T10:00:00Z",
  },
  {
    id: "2",
    type: "system_design",
    company: "Amazon",
    status: "pending",
    overall_score: null,
    completed_at: null,
    created_at: "2025-06-20T10:00:00Z",
  },
];

describe("RecentActivityList", () => {
  it("renders skeleton while loading", () => {
    const { container } = render(<RecentActivityList isLoading interviews={undefined} />);
    const skeletons = container.querySelectorAll('[class*="animate-skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders empty state when no interviews", () => {
    render(<RecentActivityList isLoading={false} interviews={[]} />);
    expect(screen.getByText("No interviews yet")).toBeInTheDocument();
  });

  it("renders list of interviews", () => {
    render(<RecentActivityList isLoading={false} interviews={mockInterviews} />);

    expect(screen.getByText("Google — coding")).toBeInTheDocument();
    expect(screen.getByText("Amazon — system_design")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Scheduled")).toBeInTheDocument();
  });

  it("displays section header", () => {
    render(<RecentActivityList isLoading={false} interviews={mockInterviews} />);
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
  });
});
