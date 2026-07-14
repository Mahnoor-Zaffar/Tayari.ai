import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  interviewSetupSchema,
  saveDraft,
  loadDraft,
  clearDraft,
  validateStep,
  DRAFT_STORAGE_KEY,
  DRAFT_TTL_MS,
  type InterviewSetupFormValues,
} from "@/features/interview/lib/wizard-schema";

const VALID_VALUES: InterviewSetupFormValues = {
  type: "coding",
  company: "Google",
  role: "Software Engineer",
  experience_level: "mid-senior",
  language: "python",
  framework: "react",
  difficulty: "medium",
  duration_minutes: 30,
  custom_instructions: undefined,
  resume_id: null,
  job_description_id: null,
  template_id: null,
  device_checks: {},
};

describe("interviewSetupSchema", () => {
  it("validates a complete form", () => {
    const result = interviewSetupSchema.safeParse(VALID_VALUES);
    expect(result.success).toBe(true);
  });

  it("rejects empty company", () => {
    const result = interviewSetupSchema.safeParse({ ...VALID_VALUES, company: "" });
    expect(result.success).toBe(false);
  });

  it("accepts empty experience_level as valid initial form state", () => {
    const result = interviewSetupSchema.safeParse({ ...VALID_VALUES, experience_level: "" });
    expect(result.success).toBe(true);
  });

  it("accepts valid experience levels", () => {
    for (const level of ["junior", "mid-senior", "staff-lead"]) {
      const result = interviewSetupSchema.safeParse({ ...VALID_VALUES, experience_level: level });
      expect(result.success).toBe(true);
    }
  });

  it("accepts duration values 15, 30, 45", () => {
    for (const d of [15, 30, 45]) {
      const result = interviewSetupSchema.safeParse({ ...VALID_VALUES, duration_minutes: d });
      expect(result.success).toBe(true);
    }
  });
});

describe("validateStep", () => {
  it("returns false for step 0 with empty company", () => {
    expect(validateStep(0, { ...VALID_VALUES, company: "" })).toBe(false);
  });

  it("returns true for step 0 with all fields filled", () => {
    expect(validateStep(0, VALID_VALUES)).toBe(true);
  });

  it("returns false for step 0 with empty experience_level", () => {
    expect(validateStep(0, { ...VALID_VALUES, experience_level: "" })).toBe(false);
  });

  it("returns false for step 1 coding without language", () => {
    expect(validateStep(1, { ...VALID_VALUES, language: null })).toBe(false);
  });

  it("returns true for step 1 coding with language", () => {
    expect(validateStep(1, VALID_VALUES)).toBe(true);
  });

  it("returns true for step 1 non-coding without language", () => {
    expect(validateStep(1, { ...VALID_VALUES, type: "behavioral", language: null })).toBe(true);
  });

  it("returns true for steps 2-4 (no validation required)", () => {
    expect(validateStep(2, VALID_VALUES)).toBe(true);
    expect(validateStep(3, VALID_VALUES)).toBe(true);
    expect(validateStep(4, VALID_VALUES)).toBe(true);
  });
});

describe("draft storage", () => {
  const mockStore: Record<string, string> = {};

  beforeEach(() => {
    Object.keys(mockStore).forEach((k) => delete mockStore[k]);
    vi.stubGlobal("localStorage", {
      getItem: vi.fn((key: string) => mockStore[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        mockStore[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete mockStore[key];
      }),
      clear: vi.fn(() => {
        Object.keys(mockStore).forEach((k) => delete mockStore[k]);
      }),
    });
  });

  it("saveDraft writes to localStorage", () => {
    saveDraft(2, { company: "Meta" });
    const raw = localStorage.getItem(DRAFT_STORAGE_KEY);
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw!);
    expect(parsed.step).toBe(2);
    expect(parsed.values.company).toBe("Meta");
    expect(parsed.savedAt).toBeDefined();
  });

  it("loadDraft returns saved draft", () => {
    saveDraft(1, { company: "Amazon" });
    const draft = loadDraft();
    expect(draft).not.toBeNull();
    expect(draft!.step).toBe(1);
    expect(draft!.values.company).toBe("Amazon");
  });

  it("loadDraft returns null when no draft exists", () => {
    expect(loadDraft()).toBeNull();
  });

  it("clearDraft removes the draft", () => {
    saveDraft(0, { company: "Google" });
    expect(localStorage.getItem(DRAFT_STORAGE_KEY)).not.toBeNull();
    clearDraft();
    expect(localStorage.getItem(DRAFT_STORAGE_KEY)).toBeNull();
  });

  it("loadDraft returns null and removes draft when expired (>24h)", () => {
    const expiredTime = new Date(Date.now() - DRAFT_TTL_MS - 1).toISOString();
    localStorage.setItem(
      DRAFT_STORAGE_KEY,
      JSON.stringify({
        step: 0,
        values: { company: "Apple" },
        savedAt: expiredTime,
      }),
    );
    expect(loadDraft()).toBeNull();
    expect(localStorage.getItem(DRAFT_STORAGE_KEY)).toBeNull();
  });

  it("loadDraft returns draft when within TTL", () => {
    const recentTime = new Date(Date.now() - 1000).toISOString();
    localStorage.setItem(
      DRAFT_STORAGE_KEY,
      JSON.stringify({
        step: 1,
        values: { company: "Tesla" },
        savedAt: recentTime,
      }),
    );
    const draft = loadDraft();
    expect(draft).not.toBeNull();
    expect(draft!.values.company).toBe("Tesla");
  });

  it("saveDraft does not throw when localStorage throws", () => {
    const spy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceeded");
    });
    expect(() => saveDraft(0, { company: "Test" })).not.toThrow();
    spy.mockRestore();
  });
});
