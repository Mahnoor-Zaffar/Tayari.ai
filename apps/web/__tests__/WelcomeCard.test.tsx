import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { WelcomeCard } from "@/features/dashboard/components/WelcomeCard";

describe("WelcomeCard", () => {
  it("renders loading state", () => {
    const { container } = render(<WelcomeCard isLoading displayName={undefined} streak={0} />);
    const skeletons = container.querySelectorAll('[class*="animate-skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders greeting with display name", () => {
    render(<WelcomeCard isLoading={false} displayName="Alice" streak={3} />);
    expect(screen.getByText(/Alice/)).toBeInTheDocument();
  });

  it("shows streak encouragement", () => {
    render(<WelcomeCard isLoading={false} displayName="Bob" streak={5} />);
    expect(screen.getByText(/5-day streak/)).toBeInTheDocument();
  });

  it("shows tip when no streak", () => {
    render(<WelcomeCard isLoading={false} displayName="Carol" streak={0} />);
    expect(screen.getByText(/Complete your first interview/)).toBeInTheDocument();
  });
});
