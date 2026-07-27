"use client";

import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";

import { AuthProvider } from "@/features/auth/hooks/use-auth";
import { getErrorMessage } from "@/lib/errors";
import { initSentry, captureException } from "@/lib/sentry";

export function Providers({ children }: { children: ReactNode }) {
  useEffect(() => {
    initSentry();
  }, []);

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            staleTime: 30_000,
          },
        },
        queryCache: new QueryCache({
          onError: (err) => {
            captureException(err, { source: "react-query" });
          },
        }),
        mutationCache: new MutationCache({
          onError: (err) => {
            captureException(err, { source: "react-query-mutation" });
          },
        }),
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
