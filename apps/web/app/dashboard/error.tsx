"use client";

import { ErrorMessage } from "@/components/error/ErrorMessage";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-8">
      <ErrorMessage message={error.message || "Failed to load dashboard"} onRetry={reset} />
    </div>
  );
}
