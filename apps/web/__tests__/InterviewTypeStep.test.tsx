import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { InterviewTypeStep } from "@/features/interview/components/steps/InterviewTypeStep";
import {
  interviewSetupSchema,
  type InterviewSetupFormValues,
} from "@/features/interview/lib/wizard-schema";
import type { InterviewOptions } from "@/features/interview/types";

const mockOptions: InterviewOptions = {
  interview_types: [
    { value: "coding", label: "Coding Interview" },
    { value: "system-design", label: "System Design" },
    { value: "behavioral", label: "Behavioral" },
  ],
  companies: ["Google", "Meta", "Amazon"],
  roles: ["Software Engineer", "Senior Software Engineer"],
  languages: [{ value: "python", label: "Python" }],
  frameworks: [{ value: "react", label: "React" }],
  experience_levels: [
    { value: "junior", label: "Junior (0-3 years)" },
    { value: "mid-senior", label: "Mid/Senior (3-7 years)" },
  ],
  difficulties: [
    { value: "easy", label: "Easy" },
    { value: "medium", label: "Medium" },
  ],
  durations: [
    { value: "15", label: "15 minutes" },
    { value: "30", label: "30 minutes" },
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

describe("InterviewTypeStep", () => {
  it("renders interview type buttons", () => {
    renderWithForm(<InterviewTypeStep options={mockOptions} isLoading={false} />);
    expect(screen.getByText("Coding Interview")).toBeInTheDocument();
    expect(screen.getByText("System Design")).toBeInTheDocument();
    expect(screen.getByText("Behavioral")).toBeInTheDocument();
  });

  it("renders company select with options", () => {
    renderWithForm(<InterviewTypeStep options={mockOptions} isLoading={false} />);
    expect(screen.getByText("Select a company")).toBeInTheDocument();
  });

  it("renders role select with options", () => {
    renderWithForm(<InterviewTypeStep options={mockOptions} isLoading={false} />);
    expect(screen.getByText("Select a role")).toBeInTheDocument();
  });

  it("renders experience level select", () => {
    renderWithForm(<InterviewTypeStep options={mockOptions} isLoading={false} />);
    expect(screen.getByText("Select your level")).toBeInTheDocument();
  });

  it("falls back to text input when no companies in options", () => {
    const emptyOptions: InterviewOptions = { ...mockOptions, companies: [], roles: [] };
    renderWithForm(<InterviewTypeStep options={emptyOptions} isLoading={false} />);
    expect(screen.getByPlaceholderText("e.g. Google")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. Software Engineer")).toBeInTheDocument();
  });

  it("shows loading state via disabled fieldset", () => {
    renderWithForm(<InterviewTypeStep options={mockOptions} isLoading={true} />);
    const fieldset = document.querySelector("fieldset");
    expect(fieldset).toBeDisabled();
  });
});
