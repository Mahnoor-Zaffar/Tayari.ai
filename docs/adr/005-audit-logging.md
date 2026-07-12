# ADR-005: Structured Audit Logging for Authentication Events

**Status:** Accepted  
**Date:** 2026-07-12  

## Context

Security events (login, logout, registration, password reset, token refresh) must be logged in a tamper-evident, queryable format. The logging must never capture sensitive data (passwords, raw tokens, full email addresses) in plaintext.

## Decision

1. **`AuthEvent` enum** — typed event names: `REGISTER`, `LOGIN`, `LOGOUT`, `LOGIN_FAILED`, `PASSWORD_RESET_REQUESTED`, `PASSWORD_RESET_COMPLETED`, `TOKEN_REFRESHED`, `TOKEN_REFRESH_REJECTED`.

2. **`AuditEvent` container** — lightweight dataclass (via `__slots__`) holding `event`, `user_id`, `email_hash` (first 16 hex chars of SHA-256, never full email), `ip_address`, `user_agent`, `request_id`, `outcome`, `failure_reason`, `metadata`.

3. **`AuditLogger`** — per-request instance pre-configured with transport-layer context (IP, User-Agent). Emits JSON via `logging.getLogger("auth.audit").info()` with `extra={"audit": json.dumps(...)}`.

4. **`auth_audit_middleware`** — FastAPI middleware extracts `X-Forwarded-For` (or `client.host`) + `User-Agent`, attaches `AuditLogger` at `request.state.audit`.

5. **Route integration** — every auth endpoint builds an `AuditEvent` and passes it to `request.state.audit.log()`.

## Consequences

- Full audit trail for all auth events without scattering logging logic across routes.
- Sensitive data is never logged — only SHA-256 email prefixes.
- Structured JSON is ingestible by log aggregators (ELK, Grafana Loki, etc.).
- `request_id` links audit events to request logs.
