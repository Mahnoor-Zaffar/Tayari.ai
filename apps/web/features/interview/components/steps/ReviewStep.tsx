"use client";

import { memo, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import { Check, ArrowRight, FileText, Mic, Clock, Code2, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { InterviewOptions } from "@/features/interview/types";
import type { InterviewSetupFormValues } from "@/features/interview/lib/wizard-schema";
import { resolveOptionLabel } from "@/features/interview/lib/config-builder";

interface ReviewStepProps {
  values: InterviewSetupFormValues;
  options?: InterviewOptions;
  isSubmitting: boolean;
  onSubmit: () => void;
  onEditStep: (step: number) => void;
  className?: string;
}

export const ReviewStep = memo(function ReviewStep({
  values,
  options,
  isSubmitting,
  onSubmit,
  onEditStep,
  className,
}: ReviewStepProps) {
  const labelFor = useCallback(
    (category: keyof InterviewOptions, value: string | null | undefined): string =>
      resolveOptionLabel(options, category, value),
    [options],
  );

  const reviewSections = useMemo(
    () => [
      {
        title: "Interview Details",
        step: 0,
        icon: Code2,
        rows: [
          { label: "Type", value: labelFor("interview_types", values.type) },
          { label: "Company", value: values.company || "—" },
          { label: "Role", value: values.role || "—" },
          { label: "Experience", value: labelFor("experience_levels", values.experience_level) },
        ],
      },
      {
        title: "Preferences",
        step: 1,
        icon: Building2,
        rows: [
          {
            label: "Language",
            value: values.language ? labelFor("languages", values.language) : "—",
          },
          {
            label: "Framework",
            value: values.framework ? labelFor("frameworks", values.framework) : "—",
          },
          { label: "Difficulty", value: labelFor("difficulties", values.difficulty) },
          { label: "Duration", value: `${values.duration_minutes} minutes` },
        ],
      },
      {
        title: "Uploads",
        step: 2,
        icon: FileText,
        rows: [
          { label: "Resume", value: values.resume_id ? "Uploaded" : "Not provided" },
          {
            label: "Job Description",
            value: values.job_description_id ? "Provided" : "Not provided",
          },
          { label: "Custom Instructions", value: values.custom_instructions ? "Yes" : "None" },
        ],
      },
      {
        title: "Device Check",
        step: 3,
        icon: Mic,
        rows: [{ label: "All checks", value: "Completed" }],
      },
    ],
    [values, options, labelFor],
  );

  return (
    <div className={cn("space-y-6", className)}>
      <div>
        <h3 className="text-lg font-semibold">Review Your Setup</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Please review your interview configuration below. You can edit any section before
          starting.
        </p>
      </div>

      {reviewSections.map((section, idx) => {
        const Icon = section.icon;
        return (
          <motion.div
            key={section.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08 }}
            className="rounded-lg border border-border bg-card"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <h4 className="text-sm font-semibold">{section.title}</h4>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => onEditStep(section.step)}
              >
                Edit
              </Button>
            </div>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-2 p-4 sm:grid-cols-2">
              {section.rows.map((row) => (
                <div key={row.label} className="flex justify-between gap-2">
                  <dt className="text-sm text-muted-foreground">{row.label}</dt>
                  <dd className="text-right text-sm font-medium">{row.value}</dd>
                </div>
              ))}
            </dl>
          </motion.div>
        );
      })}

      {/* Submit */}
      <div className="flex flex-col items-center gap-4 pt-4">
        <p className="text-sm text-muted-foreground">
          Click below to create your interview and begin your practice session.
        </p>
        <Button
          type="button"
          size="lg"
          onClick={onSubmit}
          disabled={isSubmitting}
          className="w-full sm:w-auto"
          aria-label="Create interview and start session"
        >
          {isSubmitting ? (
            <>
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
              >
                <Clock className="h-4 w-4" />
              </motion.span>
              Creating...
            </>
          ) : (
            <>
              <Check className="h-4 w-4" />
              Start Interview
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
});
