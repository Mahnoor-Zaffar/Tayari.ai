import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { SectionHeader } from "@/components/shared/SectionHeader";

describe("SectionHeader", () => {
  it("renders title and description", () => {
    render(<SectionHeader title="Section Title" description="Section description" />);
    expect(screen.getByText("Section Title")).toBeInTheDocument();
    expect(screen.getByText("Section description")).toBeInTheDocument();
  });

  it("renders without description", () => {
    render(<SectionHeader title="Only Title" />);
    expect(screen.getByText("Only Title")).toBeInTheDocument();
  });

  it("renders action element", () => {
    render(<SectionHeader title="With Action" action={<button type="button">Action</button>} />);
    expect(screen.getByText("Action")).toBeInTheDocument();
  });
});
