import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

import { QuickActions } from "@/features/dashboard/components/QuickActions";

describe("QuickActions", () => {
  it("renders all action buttons", () => {
    render(<QuickActions />);
    expect(screen.getByText("New Interview")).toBeInTheDocument();
    expect(screen.getByText("View Reports")).toBeInTheDocument();
    expect(screen.getByText("Practice")).toBeInTheDocument();
    expect(screen.getByText("Set Goal")).toBeInTheDocument();
  });

  it("renders section header", () => {
    render(<QuickActions />);
    expect(screen.getByText("Quick Actions")).toBeInTheDocument();
  });
});
