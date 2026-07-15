"use client";

import { useState, useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Play, Send, RotateCcw, Copy, Check, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { codingApi, type LanguageInfo } from "@/features/coding/api/coding";
import { useCodeExecution } from "@/features/coding/hooks/use-code-execution";
import { CODE_TEMPLATES } from "@/features/coding/lib/code-templates";
import { CodeEditor } from "./CodeEditor";
import { ProblemPanel } from "./ProblemPanel";
import { ConsoleOutput } from "./ConsoleOutput";
import { ExecutionStatus } from "./ExecutionStatus";
import { TestCasePanel } from "./TestCasePanel";
import { LanguageSelector } from "./LanguageSelector";

const STORAGE_KEY_PREFIX = "tayari-code-draft-";

interface CodeSessionProps {
  interviewId: string;
  className?: string;
}

export function CodeSession({ interviewId, className }: CodeSessionProps) {
  const { data: langsData } = useQuery({
    queryKey: ["code", "languages"],
    queryFn: () => codingApi.listLanguages(),
    staleTime: 300_000,
  });
  const languages = langsData?.languages ?? [];

  const [language, setLanguage] = useState("python");
  const [code, setCodeState] = useState(() => {
    try { return localStorage.getItem(`${STORAGE_KEY_PREFIX}${interviewId}`) || CODE_TEMPLATES["python"] || ""; }
    catch { return CODE_TEMPLATES["python"] || ""; }
  });

  const setCode = useCallback((val: string) => {
    setCodeState(val);
    try { localStorage.setItem(`${STORAGE_KEY_PREFIX}${interviewId}`, val); } catch { /* ignore */ }
  }, [interviewId]);

  const [copied, setCopied] = useState(false);
  const [testInput, setTestInput] = useState("");
  const [useCustomInput, setUseCustomInput] = useState(false);

  const { output, submission, isRunning, isSubmitting, run, submit, clearOutput } = useCodeExecution(interviewId);
  const busy = isRunning || isSubmitting;

  const handleLanguageChange = useCallback((newLang: string) => {
    setLanguage(newLang);
    const saved = localStorage.getItem(`${STORAGE_KEY_PREFIX}${interviewId}-${newLang}`);
    setCodeState(saved || CODE_TEMPLATES[newLang] || "");
  }, [interviewId]);

  const handleRun = useCallback(() => {
    run(language, code, useCustomInput ? testInput : "");
  }, [run, language, code, useCustomInput, testInput]);

  const handleSubmit = useCallback(() => {
    submit(language, code);
  }, [submit, language, code]);

  const handleReset = useCallback(() => {
    setCodeState(CODE_TEMPLATES[language] || "");
    clearOutput();
  }, [language, clearOutput]);

  const handleCopy = useCallback(async () => {
    try { await navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* ignore */ }
  }, [code]);

  return (
    <div className={cn("flex h-full flex-col overflow-hidden rounded-xl border border-border bg-background", className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
        <div className="flex items-center gap-2">
          <LanguageSelector value={language} onChange={handleLanguageChange} languages={languages} disabled={busy} />
          <div className="hidden h-4 w-px bg-border sm:block" />
          <Button type="button" variant="ghost" size="sm" onClick={handleCopy} disabled={busy} aria-label="Copy code">
            {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={handleReset} disabled={busy} aria-label="Reset to template">
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        </div>
        <ExecutionStatus
          status={isRunning ? "running" : isSubmitting ? "submitting" : output || submission ? "completed" : "idle"}
          passedCount={submission?.passed_count}
          totalCount={submission?.total_count}
          executionMs={output?.execution_ms ?? submission?.execution_ms ?? undefined}
        />
      </div>

      {/* Main content: Editor + Problem sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Problem Panel (left sidebar on desktop) */}
        <div className="hidden w-80 flex-shrink-0 overflow-y-auto border-r border-border sm:block">
          <ProblemPanel />
        </div>

        {/* Editor */}
        <div className="flex flex-1 flex-col">
          <div className="flex-1">
            <CodeEditor language={language} value={code} onChange={setCode} />
          </div>
        </div>
      </div>

      {/* Bottom panel: Console + Test cases */}
      <div className="grid grid-cols-1 border-t border-border sm:grid-cols-2">
        <ConsoleOutput output={output} submission={submission} isRunning={isRunning} isSubmitting={isSubmitting} className="h-48 sm:h-40" />
        <div className="flex flex-col border-t border-border sm:border-t-0 sm:border-l">
          <TestCasePanel testResults={submission?.test_results} totalCount={submission?.total_count} passedCount={submission?.passed_count} className="px-3 py-2" />
          <div className="flex-1 border-t border-border p-2">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                placeholder="Custom test input..."
                className="flex-1 rounded-md border border-input bg-background px-2 py-1 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                aria-label="Custom test input"
              />
              <label className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <input type="checkbox" checked={useCustomInput} onChange={(e) => setUseCustomInput(e.target.checked)} className="rounded" />
                Custom
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex items-center justify-end gap-2 border-t border-border px-3 py-2">
        <Button type="button" variant="outline" size="sm" onClick={handleRun} disabled={busy}>
          <Play className="h-3.5 w-3.5" /> Run
        </Button>
        <Button type="button" size="sm" onClick={handleSubmit} disabled={busy}>
          <Send className="h-3.5 w-3.5" /> Submit
        </Button>
      </div>
    </div>
  );
}
