"use client";

import { memo } from "react";
import { useFormContext, Controller } from "react-hook-form";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { InterviewOptions } from "@/features/interview/types";
import type { InterviewSetupFormValues } from "@/features/interview/lib/wizard-schema";

interface PreferencesStepProps {
  options?: InterviewOptions;
  isLoading: boolean;
  className?: string;
}

const DIFFICULTY_DESCRIPTIONS: Record<string, string> = {
  easy: "Warm-up level, beginner-friendly",
  medium: "Standard interview difficulty",
  hard: "Challenging, senior-level expectations",
};

const DURATION_DESCRIPTIONS: Record<string, string> = {
  "15": "Quick practice session",
  "30": "Standard interview length",
  "45": "Extended deep-dive session",
};

export const PreferencesStep = memo(function PreferencesStep({
  options,
  isLoading,
  className,
}: PreferencesStepProps) {
  const {
    control,
    watch,
    formState: { errors },
  } = useFormContext<InterviewSetupFormValues>();
  const interviewType = watch("type");

  const languages = options?.languages ?? [];
  const frameworks = options?.frameworks ?? [];
  const difficulties = options?.difficulties ?? [];
  const durations = options?.durations ?? [];

  const isCodingInterview = interviewType === "coding";
  const isSystemDesignInterview = interviewType === "system-design";

  return (
    <fieldset className={cn("space-y-6", className)} disabled={isLoading}>
      <legend className="sr-only">Interview Preferences</legend>

      {/* Programming Language */}
      <div className="space-y-2">
        <Label htmlFor="language">
          Programming Language {isCodingInterview && <span className="text-destructive">*</span>}
        </Label>
        <Controller
          name="language"
          control={control}
          render={({ field }) => (
            <Select
              value={field.value ?? ""}
              onChange={(e) => field.onChange(e.target.value || null)}
              aria-invalid={!!errors.language}
              aria-describedby={errors.language ? "language-error" : undefined}
            >
              <option value="" disabled>
                {isCodingInterview ? "Select a language" : "Optional (not required for this type)"}
              </option>
              {languages.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </Select>
          )}
        />
        {!isCodingInterview && (
          <p className="text-sm text-muted-foreground">
            Language is optional for{" "}
            {interviewType === "system-design" ? "system design" : "behavioral"} interviews.
          </p>
        )}
        {errors.language && (
          <p id="language-error" className="text-sm text-destructive" role="alert">
            {errors.language.message}
          </p>
        )}
      </div>

      {/* Spoken Language (for voice input) */}
      <div className="space-y-2">
        <Label htmlFor="spoken_language">Spoken Language (voice input)</Label>
        <Controller
          name="spoken_language"
          control={control}
          render={({ field }) => (
            <Select value={field.value ?? "en"} onChange={(e) => field.onChange(e.target.value)}>
              <option value="en">English</option>
              <option value="ur">Urdu</option>
            </Select>
          )}
        />
        <p className="text-sm text-muted-foreground">
          The language you&apos;ll speak during the interview. Used for real-time voice
          transcription.
        </p>
      </div>

      {/* System Design Problem */}
      {isSystemDesignInterview && (
        <div className="space-y-2">
          <Label htmlFor="system_design_problem">
            Design Problem <span className="text-destructive">*</span>
          </Label>
          <Controller
            name="system_design_problem"
            control={control}
            render={({ field }) => (
              <Textarea
                id="system_design_problem"
                placeholder="e.g. Design a URL shortener like Bitly"
                maxLength={500}
                value={field.value ?? ""}
                onChange={(e) => field.onChange(e.target.value || undefined)}
                aria-invalid={!!errors.system_design_problem}
                aria-describedby={
                  errors.system_design_problem ? "system-design-problem-error" : undefined
                }
              />
            )}
          />
          <p className="text-sm text-muted-foreground">
            What system should the candidate design during this interview?
          </p>
          {errors.system_design_problem && (
            <p id="system-design-problem-error" className="text-sm text-destructive" role="alert">
              {errors.system_design_problem.message}
            </p>
          )}
        </div>
      )}

      {/* Framework */}
      <div className="space-y-2">
        <Label htmlFor="framework">Framework (optional)</Label>
        <Controller
          name="framework"
          control={control}
          render={({ field }) => (
            <Select
              value={field.value ?? ""}
              onChange={(e) => field.onChange(e.target.value || null)}
            >
              <option value="">No specific framework</option>
              {frameworks.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </Select>
          )}
        />
      </div>

      {/* Difficulty */}
      <div className="space-y-2">
        <Label>Difficulty</Label>
        <Controller
          name="difficulty"
          control={control}
          render={({ field }) => (
            <div
              className="grid grid-cols-1 gap-3 sm:grid-cols-3"
              role="radiogroup"
              aria-label="Difficulty"
            >
              {difficulties.map((d) => {
                const isSelected = field.value === d.value;
                return (
                  <button
                    key={d.value}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    onClick={() => field.onChange(d.value)}
                    className={cn(
                      "rounded-lg border-2 p-3 text-left transition-all",
                      "hover:border-primary/50 hover:bg-accent/30",
                      isSelected && "border-primary bg-primary/5",
                      !isSelected && "border-border bg-card",
                    )}
                  >
                    <p className="text-sm font-semibold">{d.label}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {DIFFICULTY_DESCRIPTIONS[d.value]}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        />
      </div>

      {/* Duration */}
      <div className="space-y-2">
        <Label>Duration</Label>
        <Controller
          name="duration_minutes"
          control={control}
          render={({ field }) => (
            <div
              className="grid grid-cols-1 gap-3 sm:grid-cols-3"
              role="radiogroup"
              aria-label="Duration"
            >
              {durations.map((d) => {
                const isSelected = Number(field.value) === Number(d.value);
                return (
                  <button
                    key={d.value}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    onClick={() => field.onChange(Number(d.value))}
                    className={cn(
                      "rounded-lg border-2 p-3 text-left transition-all",
                      "hover:border-primary/50 hover:bg-accent/30",
                      isSelected && "border-primary bg-primary/5",
                      !isSelected && "border-border bg-card",
                    )}
                  >
                    <p className="text-sm font-semibold">{d.label}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {DURATION_DESCRIPTIONS[d.value]}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        />
      </div>
    </fieldset>
  );
});
