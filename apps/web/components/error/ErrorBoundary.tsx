"use client"

import { Component, type ErrorInfo, type ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { getErrorMessage } from "@/lib/errors"

interface Props {
  children: ReactNode
  /** Optional custom fallback rendered instead of the default. */
  fallback?: ReactNode
}

interface State {
  error: Error | null
}

/**
 * React error boundary that catches render-phase exceptions and displays
 * a fallback UI with a "Try again" button.
 *
 * Usage::
 *
 *    <ErrorBoundary>
 *      <MyComponent />
 *    </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ErrorBoundary caught:", error, info.componentStack)
  }

  private handleRetry = () => {
    this.setState({ error: null })
  }

  render(): ReactNode {
    if (!this.state.error) {
      return this.props.children
    }

    if (this.props.fallback) {
      return this.props.fallback
    }

    return (
      <div
        role="alert"
        className="flex min-h-[300px] flex-col items-center justify-center gap-4 p-8"
      >
        <p className="text-lg font-medium text-destructive">Something went wrong</p>
        <p className="max-w-md text-center text-sm text-muted-foreground">
          {getErrorMessage(this.state.error)}
        </p>
        <Button variant="outline" onClick={this.handleRetry}>
          Try again
        </Button>
      </div>
    )
  }
}
