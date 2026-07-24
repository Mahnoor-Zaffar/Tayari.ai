import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorMessage } from "@/components/error/ErrorMessage";

describe("ErrorMessage", () => {
  it("renders the error message text", () => {
    render(<ErrorMessage message="Something went wrong" />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("does not show retry button when onRetry is omitted", () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.queryByRole("button", { name: /try again/i })).not.toBeInTheDocument();
  });

  it("shows retry button and calls onRetry when clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorMessage message="Error" onRetry={onRetry} />);
    const btn = screen.getByRole("button", { name: /try again/i });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("applies custom className", () => {
    const { container } = render(<ErrorMessage message="Error" className="my-custom-class" />);
    expect(container.firstChild).toHaveClass("my-custom-class");
  });
});
