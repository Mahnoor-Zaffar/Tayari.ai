"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Play, Send, RotateCcw, Copy, Check, PauseIcon, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { codingApi } from "@/features/coding/api/coding";
import { useCodeExecution } from "@/features/coding/hooks/use-code-execution";
import { useInterviewSession } from "@/features/interview/hooks/use-interview-session";
import { CODE_TEMPLATES } from "@/features/coding/lib/code-templates";
import { CodeEditor } from "./CodeEditor";
import { ConsoleOutput } from "./ConsoleOutput";
import { ExecutionStatus } from "./ExecutionStatus";
import { TestCasePanel } from "./TestCasePanel";
import { LanguageSelector } from "./LanguageSelector";
import { CodingChatPanel } from "./CodingChatPanel";
import { SessionTimer } from "@/features/interview/components/session/SessionTimer";
import { SessionConnectionStatus } from "@/features/interview/components/session/ConnectionStatus";

interface CodingInterviewLayoutProps {
  sessionId: string;
  interviewId: string;
  token: string;
  language?: string | null;
  durationMinutes?: number;
  onComplete?: (sessionId: string) => void;
  className?: string;
}

interface ChatEntry {
  type: "question" | "answer" | "code_submit" | "test_result" | "hint" | "thinking";
  text: string;
  timestamp: number;
  metadata?: { passed?: number; total?: number; language?: string };
}

const STORAGE_KEY_PREFIX = "tayari-code-draft-";

export function CodingInterviewLayout({
  sessionId,
  interviewId,
  token,
  language: wizardLanguage,
  durationMinutes = 30,
  onComplete,
  className,
}: CodingInterviewLayoutProps) {
  const { data: langsData } = useQuery({
    queryKey: ["code", "languages"],
    queryFn: () => codingApi.listLanguages(),
    staleTime: 300_000,
  });
  const languages = langsData?.languages ?? [];

  const initialLanguage =
    wizardLanguage && CODE_TEMPLATES[wizardLanguage] ? wizardLanguage : "python";
  const session = useInterviewSession({
    sessionId,
    interviewId,
    token,
    durationMinutes,
    onComplete,
  });
  const codeExec = useCodeExecution(interviewId);

  const [language, setLanguage] = useState(initialLanguage);
  const [code, setCodeState] = useState(() => {
    try {
      return (
        localStorage.getItem(`${STORAGE_KEY_PREFIX}${interviewId}`) ||
        CODE_TEMPLATES[initialLanguage] ||
        ""
      );
    } catch {
      return CODE_TEMPLATES[initialLanguage] || "";
    }
  });
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const setCode = useCallback(
    (val: string) => {
      setCodeState(val);
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => {
        try {
          localStorage.setItem(`${STORAGE_KEY_PREFIX}${interviewId}`, val);
        } catch {
          /* ignore */
        }
      }, 500);
    },
    [interviewId],
  );

  const [chatEntries, setChatEntries] = useState<ChatEntry[]>([]);
  const [copied, setCopied] = useState(false);
  const [testInput, setTestInput] = useState("");
  const [useCustomInput, setUseCustomInput] = useState(false);
  const busy = codeExec.isRunning || codeExec.isSubmitting;

  const isActive = session.state.state === "active";
  const isPaused = session.state.state === "paused";

  // Sync AI questions into chat
  useEffect(() => {
    if (session.state.currentQuestion) {
      const q = session.state.currentQuestion;
      setChatEntries((prev) => {
        if (prev.some((e) => e.type === "question" && e.text === q.text)) return prev;
        return [...prev, { type: "question", text: q.text, timestamp: q.timestamp }];
      });
    }
  }, [session.state.currentQuestion]);

  // Sync code submissions into chat
  useEffect(() => {
    if (codeExec.submission) {
      const s = codeExec.submission;
      setChatEntries((prev) => [
        ...prev,
        {
          type: "code_submit",
          text: `Submitted ${s.language} code — ${s.passed_count}/${s.total_count} tests passed`,
          timestamp: Date.now(),
          metadata: { passed: s.passed_count, total: s.total_count, language: s.language },
        },
      ]);
    }
  }, [codeExec.submission]);

  const handleLanguageChange = useCallback(
    (newLang: string) => {
      setLanguage(newLang);
      const saved = localStorage.getItem(`${STORAGE_KEY_PREFIX}${interviewId}-${newLang}`);
      setCodeState(saved || CODE_TEMPLATES[newLang] || "");
    },
    [interviewId],
  );

  const handleRun = useCallback(() => {
    codeExec.run(language, code, useCustomInput ? testInput : "");
  }, [codeExec, language, code, useCustomInput, testInput]);

  const handleSubmit = useCallback(() => {
    codeExec.submit(language, code);
  }, [codeExec, language, code]);

  const handleReset = useCallback(() => {
    setCodeState(CODE_TEMPLATES[language] || "");
    codeExec.clearOutput();
  }, [language, codeExec]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }, [code]);

  return (
    <div
      className={cn(
        "flex h-full flex-col overflow-hidden rounded-xl border border-border bg-background",
        className,
      )}
    >
      {/* Top Bar */}
      <header className="flex items-center justify-between border-b border-border px-3 py-1.5">
        <div className="flex items-center gap-2">
          <SessionConnectionStatus status={session.state.connectionStatus} />
          <LanguageSelector
            value={language}
            onChange={handleLanguageChange}
            languages={languages}
            disabled={busy}
          />
          <div className="hidden h-4 w-px bg-border sm:block" />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            disabled={busy}
            aria-label="Copy code"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-success" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleReset}
            disabled={busy}
            aria-label="Reset to template"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        </div>

        <SessionTimer
          remainingSeconds={session.timer.remaining}
          elapsedSeconds={session.timer.elapsed}
          isPaused={isPaused}
          state={session.state.state}
        />

        <div className="flex items-center gap-1">
          <ExecutionStatus
            status={
              codeExec.isRunning
                ? "running"
                : codeExec.isSubmitting
                  ? "submitting"
                  : codeExec.output || codeExec.submission
                    ? "completed"
                    : "idle"
            }
            passedCount={codeExec.submission?.passed_count}
            totalCount={codeExec.submission?.total_count}
            executionMs={
              codeExec.output?.execution_ms ?? codeExec.submission?.execution_ms ?? undefined
            }
          />
          {isActive && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={session.pauseSession}
              aria-label="Pause"
            >
              <PauseIcon className="h-4 w-4" />
            </Button>
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={session.endSession}
            aria-label="End"
          >
            <Square className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main: Chat sidebar + Editor */}
      <div className="flex flex-1 overflow-hidden">
        <div className="w-72 flex-shrink-0 hidden sm:block">
          <CodingChatPanel entries={chatEntries} isAiThinking={session.state.isAiThinking} />
        </div>

        <div className="flex flex-1 flex-col">
          <div className="flex-1">
            <CodeEditor language={language} value={code} onChange={setCode} />
          </div>
        </div>
      </div>

      {/* Bottom: Console + Tests */}
      <div className="grid grid-cols-1 border-t border-border sm:grid-cols-2">
        <ConsoleOutput
          output={codeExec.output}
          submission={codeExec.submission}
          isRunning={codeExec.isRunning}
          isSubmitting={codeExec.isSubmitting}
          className="h-40"
        />
        <div className="flex flex-col border-t border-border sm:border-t-0 sm:border-l">
          <TestCasePanel
            testResults={codeExec.submission?.test_results}
            totalCount={codeExec.submission?.total_count}
            passedCount={codeExec.submission?.passed_count}
            className="px-3 py-2"
          />
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
                <input
                  type="checkbox"
                  checked={useCustomInput}
                  onChange={(e) => setUseCustomInput(e.target.checked)}
                  className="rounded"
                />
                Custom
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex items-center justify-between border-t border-border px-3 py-2">
        <div className="flex items-center gap-2" />
        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" size="sm" onClick={handleRun} disabled={busy}>
            <Play className="h-3.5 w-3.5" /> Run
          </Button>
          <Button type="button" size="sm" onClick={handleSubmit} disabled={busy}>
            <Send className="h-3.5 w-3.5" /> Submit
          </Button>
        </div>
      </div>
    </div>
  );
}
