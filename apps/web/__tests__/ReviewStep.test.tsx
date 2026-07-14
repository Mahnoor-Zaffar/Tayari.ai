import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReviewStep } from "@/features/interview/components/steps/ReviewStep";
import type { InterviewOptions } from "@/features/interview/types";
import type { InterviewSetupFormValues } from "@/features/interview/lib/wizard-schema";

const mockOptions: InterviewOptions = {
  interview_types: [
    { value: "coding", label: "Coding Interview" },
    { value: "behavioral", label: "Behavioral" },
  ],
  companies: [],
  roles: [],
  languages: [{ value: "python", label: "Python" }],
  frameworks: [{ value: "react", label: "React" }],
  experience_levels: [{ value: "mid-senior", label: "Mid/Senior (3-7 years)" }],
  difficulties: [{ value: "medium", label: "Medium" }],
  durations: [{ value: "30", label: "30 minutes" }],
};

const mockValues: InterviewSetupFormValues = {
  type: "coding",
  company: "Google",
  role: "Software Engineer",
  experience_level: "mid-senior",
  language: "python",
  framework: "react",
  difficulty: "medium",
  duration_minutes: 30,
  custom_instructions: "Focus on algorithms",
  resume_id: "abc123",
  job_description_id: null,
  template_id: null,
  device_checks: { microphone: true },
};

describe("ReviewStep", () => {
  it("renders all review sections", () => {
    render(
      <ReviewStep
        values={mockValues}
        options={mockOptions}
        isSubmitting={false}
        onSubmit={vi.fn()}
        onEditStep={vi.fn()}
      />,
    );
    expect(screen.getByText("Interview Details")).toBeInTheDocument();
    expect(screen.getByText("Preferences")).toBeInTheDocument();
    expect(screen.getByText("Uploads")).toBeInTheDocument();
    expect(screen.getByText("Device Check")).toBeInTheDocument();
  });

  it("displays company and role values", () => {
    render(
      <ReviewStep
        values={mockValues}
        options={mockOptions}
        isSubmitting={false}
        onSubmit={vi.fn()}
        onEditStep={vi.fn()}
      />,
    );
    expect(screen.getByText("Google")).toBeInTheDocument();
    expect(screen.getByText("Software Engineer")).toBeInTheDocument();
  });

  it("labels resolved from options map", () => {
    render(
      <ReviewStep
        values={mockValues}
        options={mockOptions}
        isSubmitting={false}
        onSubmit={vi.fn()}
        onEditStep={vi.fn()}
      />,
    );
    expect(screen.getByText("Coding Interview")).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("shows Start Interview button", () => {
    render(
      <ReviewStep
        values={mockValues}
        options={mockOptions}
        isSubmitting={false}
        onSubmit={vi.fn()}
        onEditStep={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /create interview and start session/i }),
    ).toBeInTheDocument();
  });

  it("calls onSubmit when Start Interview is clicked", () => {
    const onSubmit = vi.fn();
    render(
      <ReviewStep
        values={mockValues}
        options={mockOptions}
        isSubmitting={false}
        onSubmit={onSubmit}
        onEditStep={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /create interview and start session/i }));
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("calls onEditStep with correct step index when Edit clicked", () => {
    const onEditStep = vi.fn();
    render(
      <ReviewStep
        values={mockValues}
        options={mockOptions}
        isSubmitting={false}
        onSubmit={vi.fn()}
        onEditStep={onEditStep}
      />,
    );
    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[0]!);
    expect(onEditStep).toHaveBeenCalledWith(0);
  });
});
