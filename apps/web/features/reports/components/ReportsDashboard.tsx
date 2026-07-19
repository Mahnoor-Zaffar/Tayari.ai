"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, Target, Award } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useEvaluations } from "@/features/reports/hooks/use-evaluations";
import Link from "next/link";

function verdictColor(v: string | null): string {
  switch (v) {
    case "hire": return "text-success";
    case "lean_hire": return "text-warning";
    case "lean_no_hire": return "text-orange-500";
    case "no_hire": return "text-destructive";
    default: return "text-muted-foreground";
  }
}

function verdictLabel(v: string | null): string {
  switch (v) {
    case "hire": return "Hire";
    case "lean_hire": return "Lean Hire";
    case "lean_no_hire": return "Lean No-Hire";
    case "no_hire": return "No Hire";
    default: return "Pending";
  }
}

export function ReportsDashboard() {
  const { data, isLoading, isError } = useEvaluations();
  const evaluations = data?.evaluations ?? [];

  const completed = evaluations.filter((e) => e.status === "completed");
  const avgScore = completed.length
    ? completed.reduce((s, e) => s + (e.overall_score ?? 0), 0) / completed.length
    : 0;
  const best = completed.length
    ? Math.max(...completed.map((e) => e.overall_score ?? 0))
    : 0;
  const worst = completed.length
    ? Math.min(...completed.map((e) => e.overall_score ?? 0))
    : 0;

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="mt-1 text-sm text-muted-foreground">Your interview performance over time</p>
      </motion.div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={BarChart3} label="Total Interviews" value={completed.length} />
        <StatCard icon={TrendingUp} label="Average Score" value={`${(avgScore / 5 * 100).toFixed(0)}%`} />
        <StatCard icon={Target} label="Best Score" value={`${(best / 5 * 100).toFixed(0)}%`} />
        <StatCard icon={Award} label="Worst Score" value={`${(worst / 5 * 100).toFixed(0)}%`} />
      </div>

      {/* Score history */}
      {completed.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardContent className="p-4">
              <h2 className="mb-4 text-sm font-semibold flex items-center gap-2">
                <TrendingUp className="h-4 w-4" /> Score History
              </h2>
              <div className="relative h-40">
                <ScoreChart evaluations={completed} />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Recent evaluations */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
        <h2 className="mb-3 text-sm font-semibold">Recent Evaluations</h2>
        {evaluations.length === 0 && !isLoading && (
          <p className="text-sm text-muted-foreground">No evaluations yet. Complete an interview to see results here.</p>
        )}
        <div className="space-y-2">
          {evaluations.map((e, i) => (
            <Link key={e.id} href={`/dashboard/interview/${e.interview_id}/evaluation`}>
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center justify-between rounded-lg border border-border bg-card p-3 transition-colors hover:border-primary/30"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-xs font-bold">
                    {e.overall_score != null ? (e.overall_score * 20).toFixed(0) : "-"}
                  </div>
                  <div>
                  <p className="text-sm font-medium">
                    {e.created_at ? new Date(e.created_at).toLocaleDateString() : "—"}
                  </p>
                    <span className={cn("text-xs font-medium", verdictColor(e.hire_verdict))}>
                      {verdictLabel(e.hire_verdict)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {e.overall_score != null && (
                    <div className="h-2 w-20 overflow-hidden rounded-full bg-muted sm:w-32">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${(e.overall_score / 5) * 100}%` }}
                      />
                    </div>
                  )}
                  <span className="text-xs text-muted-foreground">{e.overall_score?.toFixed(1) ?? "-"}</span>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-1 py-4 text-center">
        <Icon className="h-5 w-5 text-muted-foreground" />
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}

function ScoreChart({ evaluations }: { evaluations: { overall_score: number | null; created_at: string | null }[] }) {
  const sorted = [...evaluations].reverse();
  if (sorted.length === 0) return null;

  const maxScore = 5;
  const points = sorted
    .map((e, i) => {
      const x = (i / Math.max(sorted.length - 1, 1)) * 100;
      const y = 100 - ((e.overall_score ?? 0) / maxScore) * 100;
      return `${x},${y}`;
    })
    .join(" ");
  const first = sorted[0]!;
  const last = sorted[sorted.length - 1]!;

  return (
    <svg className="h-full w-full" preserveAspectRatio="none" viewBox="0 0 100 100">
      {[0, 25, 50, 75, 100].map((v) => (
        <line key={v} x1={0} y1={v} x2={100} y2={v} stroke="hsl(var(--muted))" strokeWidth={0.3} />
      ))}
      {sorted.length > 1 && (
        <motion.polyline
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1, ease: "easeInOut" }}
          points={points}
          fill="none" stroke="hsl(var(--primary))" strokeWidth={1.5}
          vectorEffect="non-scaling-stroke"
        />
      )}
      {sorted.map((e, i) => {
        const x = (i / Math.max(sorted.length - 1, 1)) * 100;
        const y = 100 - ((e.overall_score ?? 0) / maxScore) * 100;
        return <circle key={i} cx={x} cy={y} r={2} fill="hsl(var(--primary))" />;
      })}
      <text x={0} y={105} className="fill-current text-[3px] text-muted-foreground">
        {first.created_at ? new Date(first.created_at).toLocaleDateString() : ""}
      </text>
      <text x={100} y={105} textAnchor="end" className="fill-current text-[3px] text-muted-foreground">
        {last.created_at ? new Date(last.created_at).toLocaleDateString() : ""}
      </text>
    </svg>
  );
}
