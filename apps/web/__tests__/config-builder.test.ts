import { describe, it, expect } from "vitest";
import {
  buildInterviewConfiguration,
  buildInterviewConfigurationFromResponse,
  resolveOptionLabel,
  type InterviewConfiguration,
} from "@/features/interview/lib/config-builder";
import type { InterviewSetupFormValues } from "@/features/interview/lib/wizard-schema";
import type { InterviewOptions, InterviewResponse } from "@/features/interview/types";

const FULL_VALUES: InterviewSetupFormValues = {
  type: "coding",
  company: "Google",
  role: "Software Engineer",
  experience_level: "mid-senior",
  language: "python",
  framework: "react",
  difficulty: "medium",
  duration_minutes: 30,
  custom_instructions: "Focus on algorithms",
  resume_id: "resume-uuid-123",
  job_description_id: "jd-uuid-456",
  template_id: null,

};

describe("buildInterviewConfiguration", () => {
  it("maps all fields from form values", () => {
    const config = buildInterviewConfiguration(FULL_VALUES);
    expect(config.interview_type).toBe("coding");
    expect(config.company).toBe("Google");
    expect(config.role).toBe("Software Engineer");
    expect(config.seniority).toBe("mid-senior");
    expect(config.language).toBe("python");
    expect(config.framework).toBe("react");
    expect(config.duration_minutes).toBe(30);
    expect(config.difficulty).toBe("medium");
    expect(config.resume_reference).toBe("resume-uuid-123");
    expect(config.job_description_reference).toBe("jd-uuid-456");
    expect(config.template_reference).toBeNull();
    expect(config.custom_prompt).toBe("Focus on algorithms");
  });

  it("has default device_status", () => {
    const config = buildInterviewConfiguration(FULL_VALUES);
    expect(config.device_status.microphone).toBe(false);
    expect(config.device_status.camera).toBe(false);
    expect(config.device_status.speaker).toBe(false);
    expect(config.device_status.browser).toBe(false);
    expect(config.device_status.network).toBe("unknown");
  });

  it("handles minimal form values (all optional fields null/empty)", () => {
    const minimal: InterviewSetupFormValues = {
      type: "behavioral",
      company: "Meta",
      role: "PM",
      experience_level: "junior",
      language: null,
      framework: null,
      difficulty: "easy",
      duration_minutes: 15,
      custom_instructions: undefined,
      resume_id: null,
      job_description_id: null,
      template_id: null,

    };
    const config = buildInterviewConfiguration(minimal);
    expect(config.interview_type).toBe("behavioral");
    expect(config.language).toBeNull();
    expect(config.framework).toBeNull();
    expect(config.resume_reference).toBeNull();
    expect(config.device_status.microphone).toBe(false);
  });

  it("produces a serializable object (no functions, no undefined)", () => {
    const config = buildInterviewConfiguration(FULL_VALUES);
    expect(() => JSON.stringify(config)).not.toThrow();
    const parsed = JSON.parse(JSON.stringify(config)) as InterviewConfiguration;
    expect(parsed.interview_type).toBe("coding");
    expect(parsed.company).toBe("Google");
  });
});

const MOCK_RESPONSE: InterviewResponse = {
  id: "interview-uuid-1",
  type: "system-design",
  company: "Amazon",
  role: "Senior Engineer",
  experience_level: "staff-lead",
  language: null,
  framework: null,
  difficulty: "hard",
  duration_minutes: 45,
  custom_instructions: null,
  status: "pending",
  timer_remaining: 2700,
  resume_id: null,
  job_description_id: null,
  template_id: null,
  created_at: "2025-01-15T10:00:00Z",
};

describe("buildInterviewConfigurationFromResponse", () => {
  it("maps API response fields to configuration", () => {
    const config = buildInterviewConfigurationFromResponse(MOCK_RESPONSE);
    expect(config.interview_type).toBe("system-design");
    expect(config.company).toBe("Amazon");
    expect(config.role).toBe("Senior Engineer");
    expect(config.seniority).toBe("staff-lead");
    expect(config.difficulty).toBe("hard");
    expect(config.duration_minutes).toBe(45);
    expect(config.language).toBeNull();
    expect(config.custom_prompt).toBeNull();
  });

  it("defaults device_status to all-false for API response", () => {
    const config = buildInterviewConfigurationFromResponse(MOCK_RESPONSE);
    expect(config.device_status.microphone).toBe(false);
    expect(config.device_status.camera).toBe(false);
    expect(config.device_status.speaker).toBe(false);
    expect(config.device_status.browser).toBe(false);
  });
});

const MOCK_OPTIONS: InterviewOptions = {
  interview_types: [
    { value: "coding", label: "Coding Interview" },
    { value: "system-design", label: "System Design" },
  ],
  companies: ["Google", "Meta"],
  roles: ["Software Engineer", "Senior PM"],
  languages: [{ value: "python", label: "Python" }],
  frameworks: [{ value: "react", label: "React" }],
  experience_levels: [{ value: "mid-senior", label: "Mid/Senior" }],
  difficulties: [{ value: "medium", label: "Medium" }],
  durations: [{ value: "30", label: "30 minutes" }],
};

describe("resolveOptionLabel", () => {
  it("resolves label from option items", () => {
    expect(resolveOptionLabel(MOCK_OPTIONS, "interview_types", "coding")).toBe("Coding Interview");
    expect(resolveOptionLabel(MOCK_OPTIONS, "languages", "python")).toBe("Python");
  });

  it("returns the raw value when no match found", () => {
    expect(resolveOptionLabel(MOCK_OPTIONS, "interview_types", "behavioral")).toBe("behavioral");
  });

  it("returns dash for null/undefined", () => {
    expect(resolveOptionLabel(MOCK_OPTIONS, "languages", null)).toBe("\u2014");
    expect(resolveOptionLabel(MOCK_OPTIONS, "languages", undefined)).toBe("\u2014");
  });

  it("returns raw value when options is undefined", () => {
    expect(resolveOptionLabel(undefined, "languages", "python")).toBe("python");
  });

  it("returns raw value for string array options (companies, roles)", () => {
    expect(resolveOptionLabel(MOCK_OPTIONS, "companies", "Google")).toBe("Google");
  });
});
