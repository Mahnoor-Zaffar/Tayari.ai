"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Undo2 } from "lucide-react";
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
  isSpeaking?: boolean;
  voiceError?: string | null;
  isVoiceReconnecting?: boolean;
  canUndo?: boolean;
  onAnswer: (text: string) => void;
  onRequestHint: () => void;
  onUndo?: () => void;
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
  isSpeaking = false,
  voiceError = null,
  isVoiceReconnecting = false,
  canUndo = false,
  onAnswer,
  onRequestHint,
  onUndo,
  className,
}: ConversationAreaProps) {
  const currentQuestion = questions[questions.length - 1] ?? null;

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Question Display */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {currentQuestion && <QuestionBubble question={currentQuestion} isCurrent={true} />}

        {/* Candidate Speaking Indicator */}
        {isListening && isSpeaking && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            className="flex items-center gap-2 text-sm text-muted-foreground"
          >
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
            </span>
            Speaking...
          </motion.div>
        )}

        {/* AI Thinking */}
        <AIThinkingIndicator isThinking={isAiThinking} />

        {/* Undo button — visible while AI is thinking */}
        {isAiThinking && canUndo && onUndo && (
          <motion.button
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            type="button"
            onClick={onUndo}
            className="flex items-center gap-1.5 self-end rounded-md border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <Undo2 className="h-3 w-3" />
            Undo last answer
          </motion.button>
        )}

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
          voiceError={voiceError}
          isVoiceReconnecting={isVoiceReconnecting}
          onAnswer={onAnswer}
          onRequestHint={onRequestHint}
        />
      </div>
    </div>
  );
});
