"use client";

import { memo, useCallback, useMemo, useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Check,
  ArrowRight,
  FileText,
  Mic,
  Clock,
  Code2,
  Building2,
  Brain,
  AlertTriangle,
  Save,
  ChevronDown,
  ChevronUp,
  Loader2,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { InterviewOptions } from "@/features/interview/types";
import type { InterviewSetupFormValues } from "@/features/interview/lib/wizard-schema";
import {
  resolveOptionLabel,
  buildInterviewConfiguration,
} from "@/features/interview/lib/config-builder";
import {
  useEstimateDifficulty,
  useValidateConfig,
  useCreateTemplate,
} from "@/features/interview/hooks/use-interview-setup";

interface ReviewStepProps {
  values: InterviewSetupFormValues;
  options?: InterviewOptions;
  isSubmitting: boolean;
  onSubmit: () => void;
  onEditStep: (step: number) => void;
  className?: string;
}

function difficultyColor(overall: string): string {
  switch (overall) {
    case "easy":
      return "text-success";
    case "medium":
      return "text-warning";
    case "hard":
      return "text-destructive";
    case "very_hard":
      return "text-destructive";
    default:
      return "text-muted-foreground";
  }
}

function severityColor(severity: string): string {
  switch (severity) {
    case "error":
      return "border-destructive/30 bg-destructive/5 text-destructive";
    case "warning":
      return "border-warning-border bg-warning-bg text-warning-foreground";
    case "info":
      return "border-info-border bg-info-bg text-info-foreground";
    default:
      return "border-border bg-card text-muted-foreground";
  }
}

export const ReviewStep = memo(function ReviewStep({
  values,
  options,
  isSubmitting,
  onSubmit,
  onEditStep,
  className,
}: ReviewStepProps) {
  const [showAiPreview, setShowAiPreview] = useState(false);
  const [showTemplateSave, setShowTemplateSave] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [templateSaved, setTemplateSaved] = useState(false);

  const difficultyMutation = useEstimateDifficulty();
  const validateMutation = useValidateConfig();
  const createTemplateMutation = useCreateTemplate();

  const didFetchRef = useRef(false);

  // Fetch difficulty and validation on mount
  useEffect(() => {
    if (didFetchRef.current) return;
    didFetchRef.current = true;

    const experience = values.experience_level;
    if (experience && values.company && values.role) {
      difficultyMutation.mutate({
        company: values.company,
        role: values.role,
        experience_level: experience,
        language: values.language,
      });

      validateMutation.mutate({
        type: values.type,
        company: values.company,
        role: values.role,
        experience_level: experience,
        language: values.language,
        duration_minutes: values.duration_minutes,
      });
    }
    // Run only once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
            label: "Spoken Language",
            value: values.spoken_language === "ur" ? "Urdu" : "English",
          },
          {
            label: "Framework",
            value: values.framework ? labelFor("frameworks", values.framework) : "—",
          },
          { label: "Difficulty", value: labelFor("difficulties", values.difficulty) },
          { label: "Duration", value: `${values.duration_minutes} minutes` },
          ...(values.type === "system-design" && values.system_design_problem
            ? [{ label: "Design Problem", value: values.system_design_problem }]
            : []),
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

  const aiConfig = useMemo(() => buildInterviewConfiguration(values), [values]);

  const handleSaveTemplate = useCallback(async () => {
    if (!templateName.trim()) return;
    try {
      await createTemplateMutation.mutateAsync({
        name: templateName.trim(),
        interview_type: values.type,
        company: values.company,
        role: values.role,
        experience_level: values.experience_level,
        language: values.language,
        framework: values.framework,
        difficulty: values.difficulty,
        duration_minutes: values.duration_minutes,
        custom_instructions: values.custom_instructions ?? null,
        system_design_problem: values.system_design_problem ?? null,
        resume_id: values.resume_id ?? null,
        job_description_id: values.job_description_id ?? null,
      });
      setTemplateSaved(true);
      setTimeout(() => {
        setShowTemplateSave(false);
        setTemplateSaved(false);
        setTemplateName("");
      }, 2000);
    } catch {
      // Silently handle
    }
  }, [templateName, values, createTemplateMutation]);

  return (
    <div className={cn("space-y-6", className)}>
      <div>
        <h3 className="text-lg font-semibold">Review Your Setup</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Please review your interview configuration below. You can edit any section before
          starting.
        </p>
      </div>

      {/* ── Difficulty Estimate ──────────────────────────────────────────── */}
      {difficultyMutation.data && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-border bg-card p-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3
                className={cn("h-5 w-5", difficultyColor(difficultyMutation.data.overall))}
              />
              <h4 className="text-sm font-semibold">Estimated Difficulty</h4>
            </div>
            <span
              className={cn("text-sm font-bold", difficultyColor(difficultyMutation.data.overall))}
            >
              {difficultyMutation.data.overall === "very_hard"
                ? "Very Hard"
                : difficultyMutation.data.overall.charAt(0).toUpperCase() +
                  difficultyMutation.data.overall.slice(1)}{" "}
              ({difficultyMutation.data.score.toFixed(1)}/5)
            </span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {difficultyMutation.data.description}
          </p>
          {difficultyMutation.data.factors.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {difficultyMutation.data.factors.map((f, i) => (
                <span
                  key={i}
                  className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
                >
                  {f.factor}: {f.detail}
                </span>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* ── Validation Warnings ──────────────────────────────────────────── */}
      {validateMutation.data && validateMutation.data.warnings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-warning" />
              <h4 className="text-sm font-semibold">Configuration Score</h4>
            </div>
            <span
              className={cn(
                "text-sm font-bold",
                validateMutation.data.score >= 80
                  ? "text-success"
                  : validateMutation.data.score >= 50
                    ? "text-warning"
                    : "text-destructive",
              )}
            >
              {validateMutation.data.score}%
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <motion.div
              className={cn(
                "h-full rounded-full",
                validateMutation.data.score >= 80
                  ? "bg-success"
                  : validateMutation.data.score >= 50
                    ? "bg-warning"
                    : "bg-destructive",
              )}
              initial={{ width: 0 }}
              animate={{ width: `${validateMutation.data.score}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>
          {validateMutation.data.warnings.map((w, i) => (
            <div
              key={i}
              className={cn(
                "flex items-start gap-2 rounded-lg border p-2 text-xs",
                severityColor(w.severity),
              )}
              role="alert"
            >
              <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
              <span>{w.message}</span>
            </div>
          ))}
        </motion.div>
      )}

      {/* ── Existing Review Sections ─────────────────────────────────────── */}
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

      {/* ── AI Context Preview ───────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg border border-border bg-card"
      >
        <button
          type="button"
          onClick={() => setShowAiPreview(!showAiPreview)}
          className="flex w-full items-center justify-between px-4 py-3 text-left"
          aria-expanded={showAiPreview}
        >
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <h4 className="text-sm font-semibold">AI Context Preview</h4>
          </div>
          {showAiPreview ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        <AnimatePresence>
          {showAiPreview && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden border-t border-border"
            >
              <pre className="max-h-80 overflow-auto p-4 text-xs text-muted-foreground">
                {JSON.stringify(aiConfig, null, 2)}
              </pre>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── Save as Template ─────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-3"
      >
        {!showTemplateSave ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowTemplateSave(true)}
            className="w-full"
          >
            <Save className="h-4 w-4" /> Save as Template
          </Button>
        ) : (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="space-y-2 rounded-lg border border-border bg-card p-4"
          >
            <Label htmlFor="template-name">Template Name</Label>
            <div className="flex gap-2">
              <Input
                id="template-name"
                placeholder='e.g. "Senior Backend @ Google"'
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                disabled={templateSaved}
                maxLength={100}
              />
              {templateSaved ? (
                <Button type="button" size="sm" disabled>
                  <Check className="h-4 w-4" /> Saved
                </Button>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  onClick={handleSaveTemplate}
                  disabled={!templateName.trim() || createTemplateMutation.isPending}
                >
                  {createTemplateMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  Save
                </Button>
              )}
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowTemplateSave(false);
                setTemplateName("");
                setTemplateSaved(false);
              }}
            >
              Cancel
            </Button>
          </motion.div>
        )}
      </motion.div>

      {/* ── Submit ───────────────────────────────────────────────────────── */}
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
