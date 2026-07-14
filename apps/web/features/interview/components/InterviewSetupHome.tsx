"use client";

import { memo, useCallback, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { RotateCcw, Clock, History } from "lucide-react";
import { InterviewSetupWizard } from "./InterviewSetupWizard";
import { ErrorBoundary } from "@/components/error/ErrorBoundary";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useRecentConfigs, useTemplates } from "@/features/interview/hooks/use-interview-setup";
import type { InterviewResponse } from "@/features/interview/types";

export const InterviewSetupHome = memo(function InterviewSetupHome() {
  const router = useRouter();
  const [showWizard, setShowWizard] = useState(false);

  const recentQuery = useRecentConfigs();
  const templatesQuery = useTemplates();

  const handleSuccess = useCallback(
    (interview: InterviewResponse) => {
      router.push(`/dashboard?interview=${interview.id}`);
    },
    [router],
  );

  const handleLoadConfig = useCallback(
    (interview: InterviewResponse) => {
      router.push(`/dashboard/interview/new?from=${interview.id}`);
    },
    [router],
  );

  const recentConfigs = recentQuery.data?.recent ?? [];
  const templates = templatesQuery.data?.templates ?? [];

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

      {/* ── Recent Configurations ───────────────────────────────────────── */}
      {!showWizard && recentConfigs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-border bg-card p-4"
        >
          <div className="mb-3 flex items-center gap-2">
            <History className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Recent Configurations</h3>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {recentConfigs.slice(0, 4).map((interview) => (
              <button
                key={interview.id}
                type="button"
                onClick={() => handleLoadConfig(interview)}
                className="flex flex-col items-start gap-1 rounded-lg border border-border bg-background p-3 text-left text-sm transition-colors hover:border-primary/30 hover:bg-accent/30"
              >
                <div className="flex w-full items-center justify-between gap-2">
                  <span className="font-medium truncate">
                    {interview.company} — {interview.role}
                  </span>
                  <Badge variant="outline" className="shrink-0 text-[10px]">
                    {interview.type}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {new Date(interview.created_at).toLocaleDateString()}
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── Saved Templates ─────────────────────────────────────────────── */}
      {!showWizard && templates.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-border bg-card p-4"
        >
          <div className="mb-3 flex items-center gap-2">
            <RotateCcw className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Your Templates</h3>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {templates.map((tmpl) => (
              <button
                key={tmpl.id}
                type="button"
                className="flex flex-col items-start gap-1 rounded-lg border border-border bg-background p-3 text-left text-sm transition-colors hover:border-primary/30 hover:bg-accent/30"
              >
                <span className="font-medium truncate">{tmpl.name}</span>
                {tmpl.description && (
                  <span className="text-xs text-muted-foreground line-clamp-1">
                    {tmpl.description}
                  </span>
                )}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      <ErrorBoundary>
        {showWizard ? (
          <InterviewSetupWizard onSuccess={handleSuccess} />
        ) : (
          <div className="text-center">
            <Button type="button" size="lg" onClick={() => setShowWizard(true)}>
              Start New Interview Setup
            </Button>
          </div>
        )}
      </ErrorBoundary>
    </motion.div>
  );
});
