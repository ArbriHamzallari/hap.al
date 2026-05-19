import * as Sentry from '@sentry/react'

/** Initialize Sentry before React mounts. No-op when VITE_SENTRY_DSN is unset. */
export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) return

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    sendDefaultPii: false, // CLAUDE.md §9.7 — no PII in error reports
    tracesSampleRate: import.meta.env.DEV ? 1.0 : 0.2,
  })
}
