"use client";

import { memo, useCallback } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { InterviewSetupWizard } from "./InterviewSetupWizard";
import { ErrorBoundary } from "@/components/error/ErrorBoundary";
import type { InterviewResponse } from "@/features/interview/types";

export const InterviewSetupHome = memo(function InterviewSetupHome() {
  const router = useRouter();

  const handleSuccess = useCallback(
    (interview: InterviewResponse) => {
      router.push(`/dashboard?interview=${interview.id}`);
    },
    [router],
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6 sm:py-10"
    >
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Set Up Your Interview</h1>
        <p className="mt-2 text-sm text-muted-foreground sm:text-base">
          Configure your practice session in a few quick steps
        </p>
      </div>

      <ErrorBoundary>
        <InterviewSetupWizard onSuccess={handleSuccess} />
      </ErrorBoundary>
    </motion.div>
  );
});
