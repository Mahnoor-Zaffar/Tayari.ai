"use client";

import { memo, useState } from "react";
import { motion } from "framer-motion";
import { AlertCircle, RefreshCw, BarChart3, Loader2, ArrowLeft, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useEvaluation } from "@/features/evaluation/hooks/use-evaluation";
import { ScoreCard } from "./ScoreCard";
import { RadarChart } from "./RadarChart";
import { CategoryCard } from "./CategoryCard";
import { FeedbackCard } from "./FeedbackCard";
import { RecommendationCard } from "./RecommendationCard";
import { PracticeReview } from "./PracticeReview";
import Link from "next/link";

interface EvaluationDashboardProps {
  interviewId: string;
  className?: string;
}

export const EvaluationDashboard = memo(function EvaluationDashboard({
  interviewId,
  className,
}: EvaluationDashboardProps) {
  const {
    evaluation,
    interview,
    isLoading,
    isError,
    isNotFound,
    error,
    refetch,
    triggerEvaluation,
    isTriggering,
  } = useEvaluation(interviewId);

  if (isLoading) return <EvaluationSkeleton />;

  if (isNotFound) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <Sparkles className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-xl font-bold">No evaluation yet</h2>
        <p className="text-sm text-muted-foreground">
          This interview hasn&apos;t been evaluated yet.
        </p>
        <div className="flex gap-2">
          <Button type="button" onClick={() => triggerEvaluation()} disabled={isTriggering}>
            {isTriggering ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}{" "}
            {isTriggering ? "Evaluating..." : "Run Evaluation"}
          </Button>
          <Link href="/dashboard">
            <Button type="button" variant="outline">
              <ArrowLeft className="h-4 w-4" /> Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-xl font-bold">Failed to load evaluation</h2>
        <p className="text-sm text-muted-foreground">
          {error instanceof Error ? error.message : "An unexpected error occurred."}
        </p>
        <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={refetch}>
            <RefreshCw className="h-4 w-4" /> Retry
          </Button>
          <Link href="/dashboard">
            <Button type="button" variant="outline">
              <ArrowLeft className="h-4 w-4" /> Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!evaluation || !interview) return null;

  const dims = evaluation.dimensions.map((d) => ({ key: d.key, label: d.label, score: d.score }));

  return (
    <div className={cn("mx-auto max-w-4xl space-y-8 px-4 py-8", className)}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-2xl font-bold">Interview Evaluation</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {interview.company} &middot; {interview.role} &middot; {interview.type}
        </p>
      </motion.div>

      {/* Score + Radar */}
      <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center">
        <ScoreCard
          score={evaluation.overall_score}
          score100={evaluation.overall_score_100}
          label="Overall Score"
          verdict={evaluation.hire_verdict}
        />
        <RadarChart dimensions={dims} className="hidden sm:flex" />
        <div className="flex flex-wrap gap-2 sm:hidden">
          {dims.map((d, i) => (
            <span key={d.key} className="rounded-full bg-muted px-2 py-0.5 text-[11px]">
              {d.label}: {d.score.toFixed(1)}
            </span>
          ))}
        </div>
      </div>

      {/* Category Scores */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="h-5 w-5" /> Score Breakdown
        </h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {evaluation.dimensions.map((dim, i) => (
            <CategoryCard
              key={dim.key}
              label={dim.label}
              score={dim.score}
              evidence={dim.evidence}
              index={i}
            />
          ))}
        </div>
      </section>

      {/* Feedback */}
      <FeedbackCard strengths={evaluation.strengths} improvements={evaluation.improvements} />

      {/* Recommendations */}
      {evaluation.recommendations.length > 0 && (
        <RecommendationCard recommendations={evaluation.recommendations} />
      )}

      {/* Question-by-Question Review */}
      <PracticeReview questionScores={evaluation.question_scores} />
    </div>
  );
});

function EvaluationSkeleton() {
  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <div className="flex flex-col items-center gap-4">
        <Skeleton className="h-32 w-32 rounded-full" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
      </div>
    </div>
  );
}
