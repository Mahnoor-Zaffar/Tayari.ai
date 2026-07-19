"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { Question, TranscriptEntry } from "@/features/interview/lib/session-types";
import { QuestionBubble } from "./QuestionBubble";
import { LiveTranscript } from "./LiveTranscript";
import { AIThinkingIndicator } from "./AIThinkingIndicator";
import { AnswerInput } from "./AnswerInput";
import type { ConnectionStatus as WSConnectionStatus } from "@/features/interview/lib/session-types";

interface ConversationAreaProps {
  questions: Question[];
  transcript: TranscriptEntry[];
  isAiThinking: boolean;
  connectionStatus: WSConnectionStatus;
  isPaused: boolean;
  liveTranscript?: string;
  isListening?: boolean;
  onAnswer: (text: string) => void;
  onRequestHint: () => void;
  className?: string;
}

export const ConversationArea = memo(function ConversationArea({
  questions,
  transcript,
  isAiThinking,
  connectionStatus,
  isPaused,
  liveTranscript = "",
  isListening = false,
  onAnswer,
  onRequestHint,
  className,
}: ConversationAreaProps) {
  const currentQuestion = questions[questions.length - 1] ?? null;

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Question Display */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {currentQuestion && (
          <QuestionBubble question={currentQuestion} isCurrent={true} />
        )}

        {/* AI Thinking */}
        <AIThinkingIndicator isThinking={isAiThinking} />

        {/* Live Transcript */}
        <div className="mt-6">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Transcript
          </h3>
          <LiveTranscript transcript={transcript} />
        </div>
      </div>

      {/* Answer Input */}
      <div className="border-t border-border p-4">
        <AnswerInput
          isAiThinking={isAiThinking}
          connectionStatus={connectionStatus}
          isPaused={isPaused}
          liveTranscript={liveTranscript}
          isListening={isListening}
          onAnswer={onAnswer}
          onRequestHint={onRequestHint}
        />
      </div>
    </div>
  );
});
