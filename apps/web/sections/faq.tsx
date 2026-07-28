"use client";

import { SectionTitle } from "@/components/marketing/section-title";
import { FAQItem } from "@/components/marketing/faq-item";

const FAQS = [
  {
    question: "How does the AI interviewer work?",
    answer:
      "The AI interviewer uses GPT-4o-mini to generate context-aware questions based on your target role, company, and experience level. It adapts to your answers in real time, asks follow-up questions, and probes your reasoning — just like a real interviewer.",
  },
  {
    question: "What interview formats are supported?",
    answer:
      "Tayari supports three formats: coding interviews with a live code editor and test cases, system design interviews with whiteboard-style architecture discussions, and behavioral interviews using the STAR method across 10 competency dimensions.",
  },
  {
    question: "Do I need to install anything?",
    answer:
      "No. Everything runs in your browser. You just need a modern browser with a microphone for voice interviews. The code editor, STT processing, and AI all work without downloads or plugins.",
  },
  {
    question: "How are evaluations scored?",
    answer:
      "After each interview, GPT-4o evaluates your performance across multiple dimensions (problem-solving, communication, code quality, technical depth). Each dimension gets a score from 0-5, along with a hire verdict, strengths, and specific areas for improvement.",
  },
  {
    question: "Can I practice for specific companies?",
    answer:
      "Yes. You can select your target company during setup, and the AI calibrates question difficulty and style accordingly. Company-specific prompt templates are available for Google, Meta, Amazon, and more.",
  },
  {
    question: "Is my interview data private?",
    answer:
      "Yes. Your interview transcripts and evaluations are stored securely and never shared. You can delete your data at any time. See our privacy policy for details.",
  },
];

export function FAQ() {
  return (
    <section id="faq" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          label="FAQ"
          title="Frequently asked questions"
          description="Everything you need to know about Tayari."
        />
        <div className="mt-12">
          {FAQS.map((faq) => (
            <FAQItem key={faq.question} {...faq} />
          ))}
        </div>
      </div>
    </section>
  );
}
