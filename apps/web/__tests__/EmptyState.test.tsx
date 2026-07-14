import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Mic } from "lucide-react";

import { EmptyState } from "@/components/shared/EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState icon={Mic} title="No data" description="Nothing to show yet." />);
    expect(screen.getByText("No data")).toBeInTheDocument();
    expect(screen.getByText("Nothing to show yet.")).toBeInTheDocument();
  });

  it("renders without description", () => {
    render(<EmptyState icon={Mic} title="Empty" />);
    expect(screen.getByText("Empty")).toBeInTheDocument();
  });

  it("renders action button and handles click", () => {
    const onClick = vi.fn();
    render(<EmptyState icon={Mic} title="No items" action={{ label: "Add Item", onClick }} />);

    const button = screen.getByText("Add Item");
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
