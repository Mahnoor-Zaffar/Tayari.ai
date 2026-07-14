import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { DashboardHome } from "@/features/dashboard/components/DashboardHome";

// Mock all child components to isolate DashboardHome
vi.mock("@/features/dashboard/components/WelcomeCard", () => ({
  WelcomeCard: vi.fn(() => <div data-testid="welcome-card">Welcome</div>),
}));
vi.mock("@/features/dashboard/components/StatsGrid", () => ({
  StatsGrid: vi.fn(() => <div data-testid="stats-grid">Stats</div>),
}));
vi.mock("@/features/dashboard/components/QuickActions", () => ({
  QuickActions: vi.fn(() => <div data-testid="quick-actions">Actions</div>),
}));
vi.mock("@/features/dashboard/components/RecentActivityList", () => ({
  RecentActivityList: vi.fn(() => <div data-testid="recent-activity">Recent</div>),
}));
vi.mock("@/features/dashboard/components/SubscriptionStatus", () => ({
  SubscriptionStatus: vi.fn(() => <div data-testid="subscription-status">Sub</div>),
}));
vi.mock("@/features/dashboard/components/InterviewProgress", () => ({
  InterviewProgress: vi.fn(() => <div data-testid="interview-progress">Progress</div>),
}));

// Mock auth and api hooks
const mockUseAuth = vi.fn();
const mockUseDashboard = vi.fn();
const mockUseRecentInterviews = vi.fn();

vi.mock("@/features/auth/hooks/use-auth", () => ({
  useAuth: () => mockUseAuth(),
}));
vi.mock("@/features/dashboard/hooks/use-dashboard", () => ({
  useDashboard: () => mockUseDashboard(),
  useRecentInterviews: () => mockUseRecentInterviews(),
}));

describe("DashboardHome", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ user: { display_name: "Alice" } });
    mockUseDashboard.mockReturnValue({
      data: {
        stats: {
          total_interviews: 10,
          completed_interviews: 5,
          active_interviews: 2,
          average_score: 80,
          current_streak: 3,
          credits_remaining: 50,
        },
        subscription: null,
        latest_report: null,
        user: {
          id: "1",
          email: "",
          username: "",
          display_name: "",
          email_verified: false,
          created_at: "",
        },
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    mockUseRecentInterviews.mockReturnValue({
      data: { interviews: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders all dashboard sections", () => {
    render(<DashboardHome />);

    expect(screen.getByTestId("welcome-card")).toBeInTheDocument();
    expect(screen.getByTestId("stats-grid")).toBeInTheDocument();
    expect(screen.getByTestId("quick-actions")).toBeInTheDocument();
    expect(screen.getByTestId("recent-activity")).toBeInTheDocument();
    expect(screen.getByTestId("subscription-status")).toBeInTheDocument();
    expect(screen.getByTestId("interview-progress")).toBeInTheDocument();
  });

  it("renders error state when summary query fails", () => {
    mockUseDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
      refetch: vi.fn(),
    });

    render(<DashboardHome />);
    expect(screen.getByText("Failed to load dashboard")).toBeInTheDocument();
    expect(screen.getByText("Network error")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("renders error state when recent interviews query fails", () => {
    mockUseRecentInterviews.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Recent fetch failed"),
      refetch: vi.fn(),
    });

    render(<DashboardHome />);
    expect(screen.getByText("Failed to load dashboard")).toBeInTheDocument();
    expect(screen.getByText("Recent fetch failed")).toBeInTheDocument();
  });
});
