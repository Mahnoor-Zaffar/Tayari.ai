"use client"

import { AlertCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ErrorMessageProps {
  /** Human-readable error description. */
  message: string
  /** Optional callback shown as a "Try again" button. */
  onRetry?: () => void
  /** Override or extend container styles. */
  className?: string
}

/**
 * Accessible inline error banner with an optional retry action.
 *
 * Usage::
 *
 *    <ErrorMessage message="Failed to load data" onRetry={refetch} />
 */
export function ErrorMessage({ message, onRetry, className }: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm",
        className,
      )}
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
      <div className="flex-1">
        <p className="text-destructive">{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-2" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    </div>
  )
}
