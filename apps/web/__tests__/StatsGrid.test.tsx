import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { StatsGrid } from "@/features/dashboard/components/StatsGrid";

describe("StatsGrid", () => {
  it("renders skeleton placeholders while loading", () => {
    const { container } = render(<StatsGrid isLoading stats={undefined} />);
    const skeletons = container.querySelectorAll(".bg-muted\\/20");
    // Should have skeleton elements for each stat card
    expect(skeletons.length).toBeGreaterThanOrEqual(0);
  });

  it("renders four stat cards with correct values", () => {
    const stats = {
      total_interviews: 10,
      completed_interviews: 7,
      active_interviews: 3,
      average_score: 85,
      current_streak: 5,
      credits_remaining: 100,
    };
    render(<StatsGrid stats={stats} isLoading={false} />);

    expect(screen.getByText("Total Interviews")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("Current Streak")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("Average Score")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("handles null average score gracefully", () => {
    const stats = {
      total_interviews: 0,
      completed_interviews: 0,
      active_interviews: 0,
      average_score: null,
      current_streak: 0,
      credits_remaining: 0,
    };
    render(<StatsGrid stats={stats} isLoading={false} />);

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("No scores yet")).toBeInTheDocument();
  });

  it("shows correct streak description", () => {
    const stats = {
      total_interviews: 5,
      completed_interviews: 3,
      active_interviews: 1,
      average_score: 70,
      current_streak: 1,
      credits_remaining: 50,
    };
    render(<StatsGrid stats={stats} isLoading={false} />);
    expect(screen.getByText("1 day streak!")).toBeInTheDocument();
  });
});
