import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { PreferencesStep } from "@/features/interview/components/steps/PreferencesStep";
import {
  interviewSetupSchema,
  type InterviewSetupFormValues,
} from "@/features/interview/lib/wizard-schema";
import type { InterviewOptions } from "@/features/interview/types";

const mockOptions: InterviewOptions = {
  interview_types: [],
  companies: [],
  roles: [],
  languages: [
    { value: "python", label: "Python" },
    { value: "java", label: "Java" },
  ],
  frameworks: [
    { value: "react", label: "React" },
    { value: "django", label: "Django" },
  ],
  experience_levels: [],
  difficulties: [
    { value: "easy", label: "Easy" },
    { value: "medium", label: "Medium" },
    { value: "hard", label: "Hard" },
  ],
  durations: [
    { value: "15", label: "15 minutes" },
    { value: "30", label: "30 minutes" },
    { value: "45", label: "45 minutes" },
  ],
};

function renderWithForm(ui: React.ReactNode, defaultValues?: Partial<InterviewSetupFormValues>) {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    const methods = useForm<InterviewSetupFormValues>({
      resolver: zodResolver(interviewSetupSchema) as never,
      defaultValues: {
        type: "coding",
        company: "",
        role: "",
        experience_level: "",
        language: null,
        framework: null,
        difficulty: "medium",
        duration_minutes: 30,
        custom_instructions: undefined,
        resume_id: null,
        job_description_id: null,
        template_id: null,
        device_checks: {},
        ...defaultValues,
      },
      mode: "onChange",
    });
    return <FormProvider {...methods}>{children}</FormProvider>;
  };
  return render(ui, { wrapper: Wrapper });
}

describe("PreferencesStep", () => {
  it("renders language select with options", () => {
    renderWithForm(<PreferencesStep options={mockOptions} isLoading={false} />);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Java")).toBeInTheDocument();
  });

  it("renders difficulty as radio cards", () => {
    renderWithForm(<PreferencesStep options={mockOptions} isLoading={false} />);
    expect(screen.getByText("Warm-up level, beginner-friendly")).toBeInTheDocument();
    expect(screen.getByText("Standard interview difficulty")).toBeInTheDocument();
  });

  it("renders duration options", () => {
    renderWithForm(<PreferencesStep options={mockOptions} isLoading={false} />);
    expect(screen.getByText("15 minutes")).toBeInTheDocument();
    expect(screen.getByText("30 minutes")).toBeInTheDocument();
    expect(screen.getByText("45 minutes")).toBeInTheDocument();
  });

  it("shows language as required for coding interviews", () => {
    renderWithForm(<PreferencesStep options={mockOptions} isLoading={false} />, {
      type: "coding",
    });
    expect(screen.getByText(/Programming Language/)).toBeInTheDocument();
  });

  it("shows language as optional for system-design interviews", () => {
    renderWithForm(<PreferencesStep options={mockOptions} isLoading={false} />, {
      type: "system-design",
    });
    expect(screen.getByText(/optional for system design/)).toBeInTheDocument();
  });
});
