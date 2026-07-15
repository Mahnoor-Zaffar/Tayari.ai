"use client";

import { use } from "react";
import { EvaluationDashboard } from "@/features/evaluation/components/EvaluationDashboard";

export default function EvaluationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <EvaluationDashboard interviewId={id} />;
}
