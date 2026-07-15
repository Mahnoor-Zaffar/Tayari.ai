"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, TrendingUp, Star, Lightbulb, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { interviewSetupApi } from "@/features/interview/api/interview-setup";
import { useAuth } from "@/features/auth/hooks/use-auth";
import type { AnalyzeResult } from "@/features/interview/api/interview-setup";

export default function EvaluationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [evaluation, setEvaluation] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) { router.push("/auth/login"); return; }

    const fetchEvaluation = async () => {
      try {
        const interview = await interviewSetupApi.get(id);
        setEvaluation({
          overall_score: 3.8,
          hire_verdict: "lean-hire",
          dimensions: {
            technical_communication: { score: 4.0, label: "Technical Communication" },
            problem_solving: { score: 3.5, label: "Problem Solving" },
            code_quality: { score: 4.0, label: "Code Quality" },
            language_proficiency: { score: 3.5, label: "Language Proficiency" },
          },
          strengths: ["System design thinking", "Clear communication", "Handles pressure well"],
          improvements: ["More depth on database choices", "More specific examples", "Talk through edge cases"],
          overall_assessment: "Candidate demonstrated solid engineering fundamentals and good communication skills.",
        });
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetchEvaluation();
  }, [id, user, authLoading, router]);

  if (authLoading || loading) {
    return <div className="flex h-[60vh] items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  if (!evaluation) return null;

  const score = evaluation.overall_score as number;
  const verdict = evaluation.hire_verdict as string;
  const dims = evaluation.dimensions as Record<string, { score: number; label: string }>;
  const strengths = evaluation.strengths as string[];
  const improvements = evaluation.improvements as string[];

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success/10">
          <CheckCircle2 className="h-8 w-8 text-success" />
        </div>
        <h1 className="text-2xl font-bold">Interview Complete</h1>
        <p className="mt-1 text-sm text-muted-foreground">Here&apos;s how you performed</p>
      </motion.div>

      {/* Overall Score */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-8">
            <div className="relative flex h-24 w-24 items-center justify-center">
              <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
                <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(var(--primary))" strokeWidth="8"
                  strokeDasharray={`${(score / 5) * 264} 264`} strokeLinecap="round" />
              </svg>
              <span className="absolute text-3xl font-bold">{score.toFixed(1)}</span>
            </div>
            <span className="text-sm font-medium uppercase tracking-wider text-muted-foreground">/ 5.0</span>
            <span className={cn("rounded-full px-3 py-1 text-sm font-semibold",
              verdict === "hire" && "bg-success/10 text-success",
              verdict === "lean-hire" && "bg-warning/10 text-warning",
              verdict === "no-hire" && "bg-destructive/10 text-destructive",
            )}>
              {verdict.replace("-", " ").replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </CardContent>
        </Card>
      </motion.div>

      {/* Dimensions */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="space-y-3">
        <h2 className="text-lg font-semibold flex items-center gap-2"><TrendingUp className="h-5 w-5" /> Score Breakdown</h2>
        {Object.entries(dims).map(([key, dim]) => (
          <Card key={key}>
            <CardContent className="flex items-center justify-between py-3">
              <span className="text-sm font-medium">{dim.label}</span>
              <div className="flex items-center gap-3">
                <div className="h-2 w-32 overflow-hidden rounded-full bg-muted sm:w-48">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${(dim.score / 5) * 100}%` }} />
                </div>
                <span className="text-sm font-bold tabular-nums">{dim.score.toFixed(1)}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Strengths & Improvements */}
      <div className="grid gap-4 sm:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card>
            <CardContent className="space-y-2 py-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-success"><Star className="h-4 w-4" /> Strengths</h3>
              <ul className="space-y-1">
                {strengths.map((s, i) => <li key={i} className="flex items-start gap-2 text-sm"><CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-success" />{s}</li>)}
              </ul>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
          <Card>
            <CardContent className="space-y-2 py-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-warning"><Lightbulb className="h-4 w-4" /> To Improve</h3>
              <ul className="space-y-1">
                {improvements.map((s, i) => <li key={i} className="flex items-start gap-2 text-sm"><Lightbulb className="mt-0.5 h-3 w-3 shrink-0 text-warning" />{s}</li>)}
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="text-center">
        <Button type="button" onClick={() => router.push("/dashboard")}>
          <ArrowLeft className="h-4 w-4" /> Back to Dashboard
        </Button>
      </motion.div>
    </div>
  );
}
