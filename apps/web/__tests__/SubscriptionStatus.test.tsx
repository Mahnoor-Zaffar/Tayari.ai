import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { SubscriptionStatus } from "@/features/dashboard/components/SubscriptionStatus";
import type { SubscriptionInfo } from "@/features/dashboard/types";

describe("SubscriptionStatus", () => {
  it("renders loading skeleton", () => {
    const { container } = render(<SubscriptionStatus isLoading subscription={null} />);
    const skeletons = container.querySelectorAll('[class*="animate-skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders subscription info", () => {
    const sub: SubscriptionInfo = {
      plan: "pro",
      status: "active",
      current_period_end: "2025-12-31T00:00:00Z",
    };
    render(<SubscriptionStatus subscription={sub} isLoading={false} />);

    expect(screen.getByText("Pro")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText(/Renews/)).toBeInTheDocument();
    expect(screen.getByText("Manage Plan")).toBeInTheDocument();
  });

  it("renders free plan fallback", () => {
    render(<SubscriptionStatus subscription={null} isLoading={false} />);
    expect(screen.getByText("No active subscription")).toBeInTheDocument();
    expect(screen.getByText("Upgrade to Pro")).toBeInTheDocument();
  });
});
