import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Calendar } from "lucide-react";

import { StatCard } from "@/components/shared/StatCard";

describe("StatCard", () => {
  it("renders title, value, and description", () => {
    render(<StatCard title="Total Interviews" value={42} icon={Calendar} description="All time" />);

    expect(screen.getByText("Total Interviews")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("All time")).toBeInTheDocument();
  });

  it("formats large numbers", () => {
    render(<StatCard title="Visitors" value={1234567} icon={Calendar} />);
    expect(screen.getByText("1,234,567")).toBeInTheDocument();
  });

  it("renders trend indicator", () => {
    render(
      <StatCard title="Growth" value={100} icon={Calendar} trend={{ value: 12, positive: true }} />,
    );
    expect(screen.getByText("+12% from last month")).toBeInTheDocument();
  });

  it("renders negative trend", () => {
    render(
      <StatCard title="Churn" value={5} icon={Calendar} trend={{ value: 3, positive: false }} />,
    );
    expect(screen.getByText("3% from last month")).toBeInTheDocument();
  });
});
