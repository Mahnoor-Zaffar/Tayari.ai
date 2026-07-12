"use client"

import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState, type ReactNode } from "react"

import { AuthProvider } from "@/features/auth/hooks/use-auth"
import { getErrorMessage } from "@/lib/errors"

export function Providers({ children }: { children: ReactNode }) {
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
            // Log every query error — swap with your monitoring service (Sentry,
            // DataDog, etc.) in production.
            console.error("[query]", getErrorMessage(err))
          },
        }),
        mutationCache: new MutationCache({
          onError: (err) => {
            console.error("[mutation]", getErrorMessage(err))
          },
        }),
      }),
  )

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}
