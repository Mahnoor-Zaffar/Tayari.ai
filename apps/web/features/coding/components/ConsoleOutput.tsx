"use client";

import { memo, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RunCodeResult, SubmissionResult } from "@/features/coding/api/coding";

interface ConsoleOutputProps {
  output: RunCodeResult | null;
  submission: SubmissionResult | null;
  isRunning: boolean;
  isSubmitting: boolean;
  className?: string;
}

export const ConsoleOutput = memo(function ConsoleOutput({
  output,
  submission,
  isRunning,
  isSubmitting,
  className,
}: ConsoleOutputProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [output, submission]);

  const busy = isRunning || isSubmitting;

  return (
    <div className={cn("flex flex-col rounded-lg border border-border bg-card", className)}>
      <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
        <div className="flex items-center gap-2">
          <Terminal className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-medium">Output</span>
        </div>
        {busy && <Loader2 className="h-3 w-3 animate-spin text-info" />}
      </div>
      <div className="flex-1 overflow-auto p-3 font-mono text-xs leading-relaxed">
        {busy && (
          <div className="flex items-center gap-2 text-info">
            <Loader2 className="h-3 w-3 animate-spin" />
            {isRunning ? "Running..." : "Submitting..."}
          </div>
        )}
        {!busy && !output && !submission && (
          <span className="text-muted-foreground">Run your code to see output here.</span>
        )}
        {output && !busy && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-1">
            {output.stdout && <pre className="whitespace-pre-wrap text-foreground">{output.stdout}</pre>}
            {output.stderr && <pre className="whitespace-pre-wrap text-destructive">{output.stderr}</pre>}
            {output.timed_out && <pre className="text-warning">⚠ Execution timed out</pre>}
            <div className="pt-1 text-[10px] text-muted-foreground">
              Exit: {output.exit_code} · {output.execution_ms}ms
            </div>
          </motion.div>
        )}
        {submission && !busy && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-1">
            <div className="flex items-center gap-2 pb-1">
              <span className={cn("text-sm font-bold", submission.passed_count === submission.total_count ? "text-success" : "text-warning")}>
                {submission.passed_count}/{submission.total_count} passed
              </span>
            </div>
            {submission.test_results.map((tr, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className={tr.passed ? "text-success" : "text-destructive"}>{tr.passed ? "✓" : "✗"}</span>
                <span>Test {i + 1}</span>
                {!tr.is_hidden && tr.actual_output != null && !tr.passed && (
                  <span className="text-muted-foreground">got {JSON.stringify(tr.actual_output)}</span>
                )}
              </div>
            ))}
            {submission.compiler_output && (
              <pre className="mt-2 whitespace-pre-wrap text-warning">{submission.compiler_output}</pre>
            )}
            {submission.execution_ms != null && (
              <div className="pt-1 text-[10px] text-muted-foreground">{submission.execution_ms}ms</div>
            )}
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
});
