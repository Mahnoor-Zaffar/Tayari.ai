"use client";

import { ErrorMessage } from "@/components/error/ErrorMessage";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <ErrorMessage message={error.message || "Something went wrong"} onRetry={reset} />
    </div>
  );
}
