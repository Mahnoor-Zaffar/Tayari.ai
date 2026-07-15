"use client";

import { memo } from "react";
import { CheckCircle2, XCircle, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface TestCasePanelProps {
  testResults?: Array<{ passed: boolean; is_hidden: boolean; actual_output?: string | null }>;
  totalCount?: number;
  passedCount?: number;
  className?: string;
}

export const TestCasePanel = memo(function TestCasePanel({
  testResults,
  totalCount = 0,
  passedCount = 0,
  className,
}: TestCasePanelProps) {
  if (!testResults || testResults.length === 0) return null;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center gap-2 text-sm font-medium">
        <span className={passedCount === totalCount ? "text-success" : "text-warning"}>
          {passedCount}/{totalCount}
        </span>
        <span className="text-xs text-muted-foreground">test cases</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {testResults.map((tr, i) => (
          <div
            key={i}
            className={cn(
              "flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium",
              tr.passed ? "bg-success-bg text-success-foreground" : "bg-destructive/10 text-destructive",
            )}
            title={tr.is_hidden ? "Hidden test case" : tr.actual_output ? `Got: ${tr.actual_output}` : `Test ${i + 1}`}
          >
            {tr.is_hidden ? <EyeOff className="h-3 w-3" /> : tr.passed ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
            <span>{tr.is_hidden ? "Hidden" : `Test ${i + 1}`}</span>
          </div>
        ))}
      </div>
    </div>
  );
});
