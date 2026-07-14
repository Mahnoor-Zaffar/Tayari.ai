"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/errors";
import { cn } from "@/lib/utils";

interface WidgetErrorBoundaryProps {
  children: ReactNode;
  /** Human-readable widget name shown in the fallback. */
  title?: string;
  className?: string;
}

interface WidgetErrorBoundaryState {
  error: Error | null;
}

export class WidgetErrorBoundary extends Component<
  WidgetErrorBoundaryProps,
  WidgetErrorBoundaryState
> {
  constructor(props: WidgetErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): WidgetErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error(
      `[WidgetErrorBoundary:${this.props.title ?? "unknown"}]`,
      error,
      info.componentStack,
    );
  }

  private handleRetry = () => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <div
        role="alert"
        className={cn(
          "flex flex-col items-center justify-center gap-2 rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center",
          this.props.className,
        )}
      >
        <AlertCircle className="h-5 w-5 text-destructive" />
        {this.props.title && (
          <p className="text-sm font-medium text-destructive">{this.props.title}</p>
        )}
        <p className="text-xs text-muted-foreground">{getErrorMessage(this.state.error)}</p>
        <Button variant="outline" size="sm" onClick={this.handleRetry}>
          Retry
        </Button>
      </div>
    );
  }
}
