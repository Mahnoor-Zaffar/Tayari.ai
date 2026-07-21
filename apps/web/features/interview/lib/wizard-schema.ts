import { z } from "zod";

export const WIZARD_STEPS = ["Interview Type", "Preferences", "Uploads", "Review"] as const;

export const STEP_FIELDS: Record<number, string[]> = {
  0: ["type", "company", "role", "experience_level"],
  1: ["language", "spoken_language", "framework", "difficulty", "duration_minutes"],
  2: ["custom_instructions"],
  3: [],
};

export const interviewSetupSchema = z.object({
  type: z.enum(["coding", "system-design", "behavioral"], {
    errorMap: () => ({ message: "Please select an interview type" }),
  }),
  company: z.string().min(1, "Company is required").max(100),
  role: z.string().min(1, "Role is required").max(100),
  experience_level: z.union([z.literal(""), z.enum(["junior", "mid-senior", "staff-lead"])], {
    errorMap: () => ({ message: "Please select your experience level" }),
  }),
  language: z.string().nullable().optional(),
  spoken_language: z.enum(["en", "ur"]).default("en"),
  framework: z.string().nullable().optional(),
  difficulty: z.enum(["easy", "medium", "hard"]).default("medium"),
  duration_minutes: z.union([z.literal(15), z.literal(30), z.literal(45)]).default(30),
  custom_instructions: z.string().max(2000).optional(),
  resume_id: z.string().uuid().nullable().optional(),
  job_description_id: z.string().uuid().nullable().optional(),
  template_id: z.string().uuid().nullable().optional(),
});

export type InterviewSetupFormValues = z.infer<typeof interviewSetupSchema>;

export const DRAFT_STORAGE_KEY = "interview-setup-draft";
export const DRAFT_TTL_MS = 24 * 60 * 60 * 1000;

export interface DraftData {
  step: number;
  values: Partial<InterviewSetupFormValues>;
  savedAt: string;
}

export function saveDraft(step: number, values: Partial<InterviewSetupFormValues>): void {
  if (typeof window === "undefined") return;
  try {
    const draft: DraftData = { step, values, savedAt: new Date().toISOString() };
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft));
  } catch {
    // localStorage might be full or disabled
  }
}

export function loadDraft(): DraftData | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(DRAFT_STORAGE_KEY);
    if (!raw) return null;
    const draft: DraftData = JSON.parse(raw);
    const age = Date.now() - new Date(draft.savedAt).getTime();
    if (age > DRAFT_TTL_MS) {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      return null;
    }
    return draft;
  } catch {
    return null;
  }
}

export function clearDraft(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(DRAFT_STORAGE_KEY);
  } catch {
    // ignore
  }
}

export function validateStep(step: number, values: InterviewSetupFormValues): boolean {
  const fields = STEP_FIELDS[step];
  if (!fields || fields.length === 0) return true;

  if (step === 0) {
    return !!(values.type && values.company && values.role && values.experience_level);
  }
  if (step === 1) {
    if (values.type === "coding" && !values.language) return false;
    return true;
  }
  return true;
}
