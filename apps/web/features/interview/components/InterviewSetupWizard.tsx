"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import dynamic from "next/dynamic";
import { FormProvider, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Save,
  AlertCircle,
  RotateCcw,
  CheckCircle2,
  WifiOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  interviewSetupSchema,
  type InterviewSetupFormValues,
  saveDraft,
  loadDraft,
  clearDraft,
  validateStep,
  WIZARD_STEPS,
} from "@/features/interview/lib/wizard-schema";
import { StepIndicator } from "./StepIndicator";
import { StepTransition } from "./StepTransition";
import { InterviewTypeStep } from "./steps/InterviewTypeStep";
import { PreferencesStep } from "./steps/PreferencesStep";
import { ReviewStep } from "./steps/ReviewStep";
import {
  useInterviewOptions,
  useCreateInterview,
} from "@/features/interview/hooks/use-interview-setup";
import type { InterviewResponse } from "@/features/interview/types";

const UploadsStep = dynamic(
  () => import("./steps/UploadsStep").then((m) => ({ default: m.UploadsStep })),
  { ssr: false, loading: () => <div className="h-96 animate-pulse rounded-lg bg-muted/30" /> },
);

const DEFAULT_VALUES: InterviewSetupFormValues = {
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
};

interface InterviewSetupWizardProps {
  onSuccess?: (interview: InterviewResponse) => void;
  className?: string;
}

export function InterviewSetupWizard({ onSuccess, className }: InterviewSetupWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [maxCompletedStep, setMaxCompletedStep] = useState(-1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [hasDraft, setHasDraft] = useState(false);
  const [showDraftPrompt, setShowDraftPrompt] = useState(false);
  const topRef = useRef<HTMLDivElement>(null);

  const optionsQuery = useInterviewOptions();
  const createInterviewMutation = useCreateInterview();

  const methods = useForm<InterviewSetupFormValues>({
    resolver: zodResolver(interviewSetupSchema) as never,
    defaultValues: DEFAULT_VALUES,
    mode: "onTouched",
  });

  // ── Draft recovery ──────────────────────────────────────────────────────
  useEffect(() => {
    const draft = loadDraft();
    if (draft) {
      setHasDraft(true);
      setShowDraftPrompt(true);
    }
  }, []);

  const restoreDraft = useCallback(() => {
    const draft = loadDraft();
    if (draft) {
      methods.reset({ ...DEFAULT_VALUES, ...draft.values });
      setCurrentStep(draft.step);
      setMaxCompletedStep(draft.step - 1);
    }
    setShowDraftPrompt(false);
  }, [methods]);

  const discardDraft = useCallback(() => {
    clearDraft();
    setShowDraftPrompt(false);
    setHasDraft(false);
  }, []);

  // ── Autosave (subscription-based, no re-renders) ──────────────────────────
  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    const unsubscribe = methods.watch((formData) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        saveDraft(currentStep, formData as Partial<InterviewSetupFormValues>);
      }, 1500);
    });
    return () => {
      unsubscribe.unsubscribe();
      clearTimeout(timeout);
    };
  }, [methods, currentStep]);

  // ── Step validation (watch only relevant fields) ──────────────────────────
  const [watchedType, watchedCompany, watchedRole, watchedExperienceLevel, watchedLanguage] =
    useWatch({
      control: methods.control,
      name: ["type", "company", "role", "experience_level", "language"],
    });

  const canGoNext = useMemo(() => {
    if (currentStep === 0) {
      return !!(watchedType && watchedCompany && watchedRole && watchedExperienceLevel);
    }
    if (currentStep === 1) {
      if (watchedType === "coding" && !watchedLanguage) return false;
      return true;
    }
    return true;
  }, [
    currentStep,
    watchedType,
    watchedCompany,
    watchedRole,
    watchedExperienceLevel,
    watchedLanguage,
  ]);

  // ── Navigation ──────────────────────────────────────────────────────────
  const scrollToTop = useCallback(() => {
    topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const goNext = useCallback(async () => {
    const valid = validateStep(currentStep, methods.getValues());
    if (!valid) {
      methods.trigger();
      return;
    }
    if (currentStep < WIZARD_STEPS.length - 1) {
      setMaxCompletedStep((prev) => Math.max(prev, currentStep));
      setCurrentStep((prev) => prev + 1);
      scrollToTop();
    }
  }, [currentStep, methods, scrollToTop]);

  const goBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
      scrollToTop();
    }
  }, [currentStep, scrollToTop]);

  const goToStep = useCallback(
    (step: number) => {
      if (step <= maxCompletedStep + 1) {
        setCurrentStep(step);
        scrollToTop();
      }
    },
    [maxCompletedStep, scrollToTop],
  );

  // ── Submit ───────────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const formValues = methods.getValues();
      const payload = {
        type: formValues.type,
        company: formValues.company,
        role: formValues.role,
        experience_level: formValues.experience_level,
        language: formValues.language ?? null,
        framework: formValues.framework ?? null,
        difficulty: formValues.difficulty,
        duration_minutes: formValues.duration_minutes,
        custom_instructions: formValues.custom_instructions ?? null,
        resume_id: formValues.resume_id ?? null,
        job_description_id: formValues.job_description_id ?? null,
        template_id: formValues.template_id ?? null,
      };
      const result = await createInterviewMutation.mutateAsync(payload);
      clearDraft();
      onSuccess?.(result);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Failed to create interview. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }, [methods, createInterviewMutation, onSuccess]);

  // ── Keyboard ────────────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      )
        return;
      if (e.key === "ArrowRight" && !e.shiftKey && currentStep < WIZARD_STEPS.length - 1) {
        e.preventDefault();
        goNext();
      }
      if (e.key === "ArrowLeft" && !e.shiftKey && currentStep > 0) {
        e.preventDefault();
        goBack();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [currentStep, goNext, goBack]);

  return (
    <FormProvider {...methods}>
      {/* Draft Recovery Prompt */}
      <AnimatePresence>
        {showDraftPrompt && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-4 flex items-center justify-between gap-3 rounded-lg border border-warning-border bg-warning-bg p-4"
            role="alert"
          >
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-warning" />
              <div>
                <p className="text-sm font-semibold">Saved draft found</p>
                <p className="text-xs text-muted-foreground">
                  Would you like to continue where you left off?
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="button" size="sm" variant="outline" onClick={discardDraft}>
                Discard
              </Button>
              <Button type="button" size="sm" onClick={restoreDraft}>
                <RotateCcw className="h-3 w-3" /> Restore
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Card className={cn("relative", className)}>
        <CardHeader>
          <div ref={topRef} />
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold tracking-tight">Interview Setup</h2>
                <p className="text-sm text-muted-foreground">
                  Step {currentStep + 1} of {WIZARD_STEPS.length}: {WIZARD_STEPS[currentStep]}
                </p>
              </div>
              {hasDraft && !showDraftPrompt && (
                <Badge variant="secondary" className="gap-1">
                  <Save className="h-3 w-3" /> Auto-saved
                </Badge>
              )}
            </div>
            <StepIndicator
              currentStep={currentStep}
              maxCompletedStep={maxCompletedStep}
              onStepClick={goToStep}
            />
          </div>
        </CardHeader>

        <CardContent className="min-h-[300px]">
          {optionsQuery.isError && (
            <div
              className="mb-4 flex items-center justify-between gap-2 rounded-lg bg-destructive/10 p-3"
              role="alert"
            >
              <div className="flex items-center gap-2">
                <WifiOff className="h-4 w-4 text-destructive" />
                <p className="text-sm text-destructive">Failed to load interview options.</p>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => optionsQuery.refetch()}
              >
                <RotateCcw className="h-3 w-3" /> Retry
              </Button>
            </div>
          )}
          <StepTransition step={currentStep}>
            {currentStep === 0 && (
              <InterviewTypeStep options={optionsQuery.data} isLoading={optionsQuery.isLoading} />
            )}
            {currentStep === 1 && (
              <PreferencesStep options={optionsQuery.data} isLoading={optionsQuery.isLoading} />
            )}
            {currentStep === 2 && <UploadsStep />}
            {currentStep === 3 && (
              <ReviewStep
                values={methods.getValues()}
                options={optionsQuery.data}
                isSubmitting={isSubmitting}
                onSubmit={handleSubmit}
                onEditStep={goToStep}
              />
            )}
          </StepTransition>

          {submitError && (
            <div
              className="mt-4 flex items-center justify-between gap-2 rounded-lg bg-destructive/10 p-3"
              role="alert"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <p className="text-sm text-destructive">{submitError}</p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handleSubmit}>
                <RotateCcw className="h-3 w-3" /> Retry
              </Button>
            </div>
          )}
        </CardContent>

        {currentStep < 3 && (
          <CardFooter className="flex items-center justify-between border-t border-border pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={goBack}
              disabled={currentStep === 0}
              aria-label="Go to previous step"
            >
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                onClick={goNext}
                disabled={!canGoNext}
                aria-label="Go to next step"
              >
                Next <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </CardFooter>
        )}
      </Card>
    </FormProvider>
  );
}
