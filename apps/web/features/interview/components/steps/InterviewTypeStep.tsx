"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Code2, Layout, MessageSquare, Building2, Briefcase, GraduationCap } from "lucide-react";
import { useFormContext, Controller } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { InterviewOptions } from "@/features/interview/types";
import type { InterviewSetupFormValues } from "@/features/interview/lib/wizard-schema";

interface InterviewTypeStepProps {
  options?: InterviewOptions;
  isLoading: boolean;
  className?: string;
}

const INTERVIEW_TYPE_ICONS: Record<string, typeof Code2> = {
  coding: Code2,
  "system-design": Layout,
  behavioral: MessageSquare,
};

export const InterviewTypeStep = memo(function InterviewTypeStep({
  options,
  isLoading,
  className,
}: InterviewTypeStepProps) {
  const {
    register,
    control,
    formState: { errors },
  } = useFormContext<InterviewSetupFormValues>();

  const interviewTypes = options?.interview_types ?? [];
  const companies = options?.companies ?? [];
  const roles = options?.roles ?? [];
  const experienceLevels = options?.experience_levels ?? [];

  return (
    <fieldset className={cn("space-y-6", className)} disabled={isLoading}>
      <legend className="sr-only">Interview Type and Company Details</legend>

      {/* Interview Type */}
      <div className="space-y-3">
        <Label htmlFor="type">
          Interview Type <span className="text-destructive">*</span>
        </Label>
        <Controller
          name="type"
          control={control}
          render={({ field }) => (
            <div
              className="grid grid-cols-1 gap-3 sm:grid-cols-3"
              role="radiogroup"
              aria-label="Interview type"
            >
              {interviewTypes.map((opt) => {
                const Icon = INTERVIEW_TYPE_ICONS[opt.value] ?? Code2;
                const isSelected = field.value === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    onClick={() => field.onChange(opt.value)}
                    className={cn(
                      "flex flex-col items-start gap-2 rounded-lg border-2 p-4 text-left transition-all",
                      "hover:border-primary/50 hover:bg-accent/30",
                      isSelected && "border-primary bg-primary/5 ring-4 ring-primary/10",
                      !isSelected && "border-border bg-card",
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-6 w-6",
                        isSelected ? "text-primary" : "text-muted-foreground",
                      )}
                    />
                    <div>
                      <p className="text-sm font-semibold">{opt.label}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        />
        {errors.type && (
          <p id="type-error" className="text-sm text-destructive" role="alert">
            {errors.type.message}
          </p>
        )}
      </div>

      {/* Company */}
      <div className="space-y-2">
        <Label htmlFor="company">
          Company <span className="text-destructive">*</span>
        </Label>
        {companies.length > 0 ? (
          <Controller
            name="company"
            control={control}
            render={({ field }) => (
              <div className="relative">
                <Building2
                  className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                  aria-hidden="true"
                />
                <Select
                  value={field.value}
                  onChange={field.onChange}
                  className="pl-9"
                  aria-invalid={!!errors.company}
                  aria-describedby={errors.company ? "company-error" : undefined}
                >
                  <option value="" disabled>
                    Select a company
                  </option>
                  {companies.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              </div>
            )}
          />
        ) : (
          <div className="relative">
            <Building2
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              id="company"
              placeholder="e.g. Google"
              className="pl-9"
              aria-invalid={!!errors.company}
              aria-describedby={errors.company ? "company-error" : undefined}
              {...register("company")}
            />
          </div>
        )}
        {errors.company && (
          <p id="company-error" className="text-sm text-destructive" role="alert">
            {errors.company.message}
          </p>
        )}
      </div>

      {/* Role */}
      <div className="space-y-2">
        <Label htmlFor="role">
          Role <span className="text-destructive">*</span>
        </Label>
        {roles.length > 0 ? (
          <Controller
            name="role"
            control={control}
            render={({ field }) => (
              <div className="relative">
                <Briefcase
                  className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                  aria-hidden="true"
                />
                <Select
                  value={field.value}
                  onChange={field.onChange}
                  className="pl-9"
                  aria-invalid={!!errors.role}
                  aria-describedby={errors.role ? "role-error" : undefined}
                >
                  <option value="" disabled>
                    Select a role
                  </option>
                  {roles.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </Select>
              </div>
            )}
          />
        ) : (
          <div className="relative">
            <Briefcase
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              id="role"
              placeholder="e.g. Software Engineer"
              className="pl-9"
              aria-invalid={!!errors.role}
              aria-describedby={errors.role ? "role-error" : undefined}
              {...register("role")}
            />
          </div>
        )}
        {errors.role && (
          <p id="role-error" className="text-sm text-destructive" role="alert">
            {errors.role.message}
          </p>
        )}
      </div>

      {/* Experience Level */}
      <div className="space-y-2">
        <Label htmlFor="experience_level">
          Experience Level <span className="text-destructive">*</span>
        </Label>
        <Controller
          name="experience_level"
          control={control}
          render={({ field }) => (
            <div className="relative">
              <GraduationCap
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />
              <Select
                value={field.value}
                onChange={field.onChange}
                className="pl-9"
                aria-invalid={!!errors.experience_level}
                aria-describedby={errors.experience_level ? "exp-error" : undefined}
              >
                <option value="" disabled>
                  Select your level
                </option>
                {experienceLevels.map((e) => (
                  <option key={e.value} value={e.value}>
                    {e.label}
                  </option>
                ))}
              </Select>
            </div>
          )}
        />
        {errors.experience_level && (
          <p id="exp-error" className="text-sm text-destructive" role="alert">
            {errors.experience_level.message}
          </p>
        )}
      </div>
    </fieldset>
  );
});
