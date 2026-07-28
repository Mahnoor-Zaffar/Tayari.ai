"use client";

import {
  Brain,
  Code,
  Mic,
  FileText,
  MessageSquare,
  BarChart3,
  Cpu,
  GitBranch,
  Monitor,
  Zap,
  Network,
  BookOpen,
} from "lucide-react";
import { SectionTitle } from "@/components/marketing/section-title";
import { FeatureCard } from "@/components/marketing/feature-card";

const FEATURES = [
  {
    icon: Brain,
    title: "AI Interviewer",
    description:
      "Natural conversations with an AI that adapts to your answers, asks follow-ups, and probes like a real interviewer.",
  },
  {
    icon: Code,
    title: "Coding Challenges",
    description:
      "Solve problems in a live Monaco editor with syntax highlighting, test cases, and real-time code evaluation across 7 languages.",
  },
  {
    icon: Mic,
    title: "Voice Interviews",
    description:
      "Speak your answers naturally. Deepgram STT transcribes in real-time with configurable silence detection.",
  },
  {
    icon: FileText,
    title: "Resume Analysis",
    description:
      "Upload your resume and the AI tailors questions to your experience and target role.",
  },
  {
    icon: MessageSquare,
    title: "Conversation Memory",
    description:
      "The AI remembers your earlier answers and builds on them across the entire interview.",
  },
  {
    icon: BarChart3,
    title: "Detailed Reports",
    description:
      "Multi-dimensional scoring across problem-solving, communication, code quality, and technical depth.",
  },
  {
    icon: Cpu,
    title: "System Design",
    description:
      "Whiteboard-style architecture discussions with probing questions on scale, trade-offs, and failure modes.",
  },
  {
    icon: GitBranch,
    title: "Behavioral Interviews",
    description:
      "STAR-method coaching with competency dimensions like leadership, conflict resolution, and ownership.",
  },
  {
    icon: Monitor,
    title: "Dashboard & Analytics",
    description:
      "Track your progress with stats, trends, and performance metrics across every practice session.",
  },
  {
    icon: Zap,
    title: "Instant Feedback",
    description:
      "Get scored results immediately after each interview with actionable improvement suggestions.",
  },
  {
    icon: Network,
    title: "Session Resilience",
    description:
      "Automatic reconnection with state replay. Never lose your interview to a network issue.",
  },
  {
    icon: BookOpen,
    title: "Company-Specific Prep",
    description:
      "Practice with interview styles calibrated to Google, Meta, Amazon, and other top tech companies.",
  },
];

export function Features() {
  return (
    <section id="features" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="Features"
          title="Everything you need to ace your interview"
          description="Three interview modalities, AI-powered evaluation, and detailed analytics — all in one platform."
        />
        <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {FEATURES.map((feature, i) => (
            <FeatureCard key={feature.title} {...feature} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
