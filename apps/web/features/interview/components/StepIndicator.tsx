"use client";

import { memo } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { WIZARD_STEPS } from "@/features/interview/lib/wizard-schema";

interface StepIndicatorProps {
  currentStep: number;
  maxCompletedStep: number;
  onStepClick?: (step: number) => void;
  className?: string;
}

export const StepIndicator = memo(function StepIndicator({
  currentStep,
  maxCompletedStep,
  onStepClick,
  className,
}: StepIndicatorProps) {
  return (
    <nav aria-label="Progress" className={cn("w-full", className)}>
      <ol className="flex flex-row gap-2 sm:gap-4">
        {WIZARD_STEPS.map((label, idx) => {
          const isCompleted = idx < currentStep || idx <= maxCompletedStep;
          const isCurrent = idx === currentStep;
          const isClickable = idx <= maxCompletedStep + 1 && onStepClick;
          return (
            <li key={label} className="flex flex-1 flex-col items-center gap-2">
              <button
                type="button"
                disabled={!isClickable}
                onClick={() => isClickable && onStepClick?.(idx)}
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-semibold transition-all",
                  isCompleted && "border-primary bg-primary text-primary-foreground",
                  isCurrent &&
                    !isCompleted &&
                    "border-primary bg-background text-primary ring-4 ring-primary/20",
                  !isCompleted && !isCurrent && "border-border bg-background text-muted-foreground",
                  isClickable && "cursor-pointer hover:ring-2 hover:ring-primary/20",
                  !isClickable && "cursor-not-allowed opacity-60",
                )}
                aria-label={`Step ${idx + 1}: ${label}`}
                aria-current={isCurrent ? "step" : undefined}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : <span>{idx + 1}</span>}
              </button>
              <span
                className={cn(
                  "hidden text-center text-xs font-medium sm:block",
                  isCurrent ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {label}
              </span>
              {idx < WIZARD_STEPS.length - 1 && (
                <div className="hidden h-px flex-1 bg-border lg:block" aria-hidden="true" />
              )}
            </li>
          );
        })}
      </ol>
      <div className="mt-3 sm:hidden">
        <p className="text-sm text-muted-foreground">
          Step {currentStep + 1} of {WIZARD_STEPS.length}: {WIZARD_STEPS[currentStep]}
        </p>
      </div>
    </nav>
  );
});
