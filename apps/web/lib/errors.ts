import { ApiError } from "@/lib/api/client"

/**
 * Normalised error details extracted from any thrown value.
 */
export interface ErrorDetails {
  code: string
  message: string
  status?: number
  details?: unknown[]
  requestId?: string
}

/**
 * Extract a standard ``ErrorDetails`` object from any thrown value.
 *
 * - ``ApiError`` → preserves code, message, status, details, requestId
 * - ``Error``   → code ``"UNKNOWN"``, message from ``.message``
 * - everything else → generic fallback
 */
export function getErrorDetails(err: unknown): ErrorDetails {
  if (err instanceof ApiError) {
    return {
      code: err.code,
      message: err.message,
      status: err.status,
      details: err.details,
      requestId: err.requestId,
    }
  }

  if (err instanceof Error) {
    return { code: "UNKNOWN", message: err.message }
  }

  return { code: "UNKNOWN", message: "An unexpected error occurred" }
}

/**
 * Extract a human-readable message from any thrown value.
 * Convenience wrapper around ``getErrorDetails`` for inline usage.
 */
export function getErrorMessage(err: unknown): string {
  return getErrorDetails(err).message
}

/**
 * Convenience type guard.
 */
export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError
}
