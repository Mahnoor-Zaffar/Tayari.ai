"use client";

import { memo, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, ChevronDown, ChevronUp, Edit3, X, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { QuestionScoreData, DimensionData } from "../api/evaluation";

interface PracticeReviewProps {
  questionScores: QuestionScoreData[];
  className?: string;
}

interface QuestionCardProps {
  qa: QuestionScoreData;
  index: number;
}

function scoreColor(score: number): string {
  if (score >= 4) return "text-success";
  if (score >= 3) return "text-warning";
  return "text-destructive";
}

function scoreBarColor(score: number): string {
  if (score >= 4) return "bg-success";
  if (score >= 3) return "bg-warning";
  return "bg-destructive";
}

const DimensionBar = memo(function DimensionBar({
  dimension,
  index,
}: {
  dimension: DimensionData;
  index: number;
}) {
  const pct = (dimension.score / 5) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className="space-y-1"
    >
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{dimension.label}</span>
        <span className={cn("font-medium tabular-nums", scoreColor(dimension.score))}>
          {dimension.score.toFixed(1)}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className={cn("h-full rounded-full", scoreBarColor(dimension.score))}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, delay: index * 0.05 + 0.1, ease: "easeOut" }}
        />
      </div>
      {dimension.evidence && (
        <p className="text-[11px] text-muted-foreground italic mt-0.5">
          &ldquo;{dimension.evidence}&rdquo;
        </p>
      )}
    </motion.div>
  );
});

const QuestionCard = memo(function QuestionCard({ qa, index }: QuestionCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isReAnswering, setIsReAnswering] = useState(false);
  const [reAnswer, setReAnswer] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleReAnswer = useCallback(() => {
    setIsReAnswering(true);
    setReAnswer("");
  }, []);

  const handleSubmitReAnswer = useCallback(() => {
    if (reAnswer.trim()) {
      setSubmitted(true);
      setIsReAnswering(false);
    }
  }, [reAnswer]);

  const handleCancelReAnswer = useCallback(() => {
    setIsReAnswering(false);
    setReAnswer("");
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.3 }}
      className="rounded-lg border border-border bg-card overflow-hidden"
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between p-4 text-left hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-bold">
            {index + 1}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{qa.question_text}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Score:{" "}
              <span className={cn("font-medium", scoreColor(qa.overall_score))}>
                {qa.overall_score.toFixed(1)}
              </span>
              /5
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
      </button>

      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4 border-t border-border">
              {/* Question */}
              <div className="mt-4">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                  Question
                </p>
                <p className="text-sm">{qa.question_text}</p>
              </div>

              {/* Answer */}
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                  Your Answer
                </p>
                <p className="text-sm text-muted-foreground">{qa.answer_text}</p>
              </div>

              {/* Dimension Scores */}
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Dimension Scores
                </p>
                <div className="space-y-3">
                  {qa.dimension_scores.map((dim, i) => (
                    <DimensionBar key={dim.key} dimension={dim} index={i} />
                  ))}
                </div>
              </div>

              {/* Feedback */}
              {qa.feedback && (
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                    Feedback
                  </p>
                  <p className="text-sm">{qa.feedback}</p>
                </div>
              )}

              {/* Re-answer Section */}
              <div className="pt-2 border-t border-border">
                {submitted && !isReAnswering && (
                  <div className="mb-3 rounded-md bg-success/10 p-3">
                    <p className="text-xs font-medium text-success mb-1">Practice Answer Saved</p>
                    <p className="text-sm">{reAnswer}</p>
                  </div>
                )}

                {isReAnswering ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Type Your Improved Answer
                    </p>
                    <textarea
                      value={reAnswer}
                      onChange={(e) => setReAnswer(e.target.value)}
                      placeholder="Type a better answer here for practice..."
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary min-h-[100px] resize-y"
                      autoFocus
                    />
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleSubmitReAnswer}
                        disabled={!reAnswer.trim()}
                        className={cn(
                          "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                          reAnswer.trim()
                            ? "bg-primary text-primary-foreground hover:bg-primary/90"
                            : "bg-muted text-muted-foreground cursor-not-allowed",
                        )}
                      >
                        <Check className="h-3.5 w-3.5" />
                        Submit
                      </button>
                      <button
                        onClick={handleCancelReAnswer}
                        className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <X className="h-3.5 w-3.5" />
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={handleReAnswer}
                    className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                  >
                    <Edit3 className="h-3.5 w-3.5" />
                    Re-answer this question
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
});

export const PracticeReview = memo(function PracticeReview({
  questionScores,
  className,
}: PracticeReviewProps) {
  if (questionScores.length === 0) {
    return (
      <div className={cn("rounded-lg border border-border bg-card p-6 text-center", className)}>
        <MessageSquare className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">
          No question-by-question evaluation available.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center gap-2">
        <MessageSquare className="h-5 w-5 text-primary" />
        <h3 className="text-sm font-semibold">Question-by-Question Review</h3>
        <span className="text-xs text-muted-foreground">({questionScores.length} questions)</span>
      </div>
      <div className="space-y-3">
        {questionScores.map((qa, i) => (
          <QuestionCard key={qa.question_index} qa={qa} index={i} />
        ))}
      </div>
    </div>
  );
});
