"use client";

import { use } from "react";
import { CodeSession } from "@/features/coding/components/CodeSession";
import { Skeleton } from "@/components/ui/skeleton";

export default function CodingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col p-2 sm:p-4">
      <CodeSession interviewId={id} />
    </div>
  );
}
