import * as Sentry from "@sentry/browser";

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN ?? "";

let initialized = false;

export function initSentry() {
  if (initialized || !SENTRY_DSN) return;
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: process.env.NODE_ENV ?? "development",
    release: `tayari-web@${process.env.NEXT_PUBLIC_APP_VERSION ?? "0.1.0"}`,
    tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,
  });
  initialized = true;
}

export function captureException(error: unknown, context?: Record<string, unknown>) {
  if (!SENTRY_DSN) return;
  initSentry();
  Sentry.withScope((scope) => {
    if (context) scope.setExtras(context);
    Sentry.captureException(error);
  });
}

export function captureMessage(message: string, level: Sentry.SeverityLevel = "error") {
  if (!SENTRY_DSN) return;
  initSentry();
  Sentry.captureMessage(message, level);
}
