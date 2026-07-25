# Tayari AI — Architecture & Operations Reference

**Domain**: AI-powered interview coaching platform — real-time voice/coding/system-design interviews with automated evaluation
**Tech Stack**: Python 3.13 / FastAPI + SQLAlchemy async / PostgreSQL 17 / Redis 7 / WebSocket (session engine) + Next.js 15 (React 19) / Tailwind v4 / Monaco Editor / Deepgram STT / OpenAI (via OpenRouter) / Resend (email)
**Scale**: Single-tenant capable (free tier caps 10 interviews/user); multi-engineer open-source project
**Deployment**: Docker Compose (dev) with Traefik reverse-proxy config available; production CI builds images but deploy target is placeholder (Render/Railway/Fly.io)
**Repository**: monorepo — pnpm workspaces (6 packages), TurboRepo task orchestration, uv for Python dependency management

---

## 1. System Architecture

### 1.1 Component Diagram (text)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser (Next.js 15)                        │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Interview │  │ Dashboard /  │  │ Monaco     │  │ Whiteboard   │  │
│  │ Session   │  │ Reports      │  │ Code       │  │ (Excalidraw) │  │
│  │ (WebSocket)│  │ (REST)       │  │ Editor     │  │              │  │
│  └─────┬─────┘  └──────┬───────┘  └─────┬──────┘  └──────┬───────┘  │
│        │               │                │               │           │
└────────┼───────────────┼────────────────┼───────────────┼───────────┘
         │               │                │               │
    ┌────▼───────────────▼────────────────▼───────────────▼──────────┐
    │                    FastAPI (Uvicorn)                           │
    │  ┌────────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐ │
    │  │ Auth JWT   │  │ REST     │  │ WebSocket│  │ Background   │ │
    │  │ (RS256)    │  │ Routers  │  │ Session  │  │ APScheduler  │ │
    │  └────────────┘  └──────────┘  │ Engine   │  │ (Evaluation) │ │
    │                                └────┬─────┘  └──────────────┘ │
    │  ┌──────────────────────────────────┼────────────────────────┐ │
    │  │         AI Orchestrator          │                       │ │
    │  │  ┌──────────┐ ┌───────────────┐ │ ┌──────────────────┐  │ │
    │  │  │ OpenAI   │ │ Conversation  │ │ │ Prompt Builder   │  │ │
    │  │  │ Provider │ │ Memory (20-tn)│ │ │ (packages/       │  │ │
    │  │  └──────────┘ └───────────────┘ │ │  prompts/*.md)   │  │ │
    │  └────────────────────────────────┘ └──────────────────┘  │ │
    └───────────────────────────────────────────────────────────────┘
         │               │
    ┌────▼───────────────▼──────────────────────────────────────────┐
    │                    Data Layer                                  │
    │  ┌─────────────────────┐  ┌────────────────────────────────┐  │
    │  │ PostgreSQL 17       │  │  Redis 7                       │  │
    │  │ - asyncpg           │  │  - Celery broker (future)      │  │
    │  │ - SQLAlchemy 2.0    │  │  - Rate limiting (future)      │  │
    │  │ - Alembic (8 migr.) │  │  - Session heartbeat           │  │
    │  └─────────────────────┘  └────────────────────────────────┘  │
    └───────────────────────────────────────────────────────────────┘
```

### 1.2 Service Boundaries

| Module | Responsibility | Key Files |
|--------|---------------|-----------|
| `features/auth/` | Registration, login, JWT, email verification, password reset | `guard.py`, `services.py`, `jwt/service.py` |
| `features/interview/` | Interview CRUD, setup wizard, configuration snapshots | `routes.py`, `service.py`, `models.py` |
| `ai/realtime/` | Live interview state machine, AI turn loop, WebSocket session mgmt | `session_manager.py`, `orchestrator.py`, `state_machine.py` |
| `features/sessions/` | Session persistence, reconnect, event history | `routes.py`, `service.py` |
| `features/reports/` | Evaluation pipeline, score persistence, report retrieval | `service.py`, `routes.py` |
| `workers/` | Background evaluation via APScheduler | `scheduler.py`, `evaluation.py` |
| `features/billing/` | Stripe stubs — routes defined but all return "Not implemented" | `routes.py`, `services.py` |
| `features/email/` | Transactional email via Resend (verify, reset) | `service.py` |
| `features/voice/` | Deepgram STT integration | `deepgram_service.py` |
| `features/code/` | Code review + submission storage | `routes.py`, `service.py` |
| `features/dashboard/` | Aggregated stats + recent activity | `router.py`, `service.py` |
| `features/analytics/` | Usage analytics | `router.py` |
| `features/admin/` | Admin user management | `features/users/` |

### 1.3 What This System Does vs. Does NOT

**Does:**
- Simulates live technical interviews across 3 modalities (coding, system-design, behavioral)
- Streams AI interviewer responses token-by-token via WebSocket
- Captures voice input via browser mic → Deepgram STT (or typed answers)
- Evaluates completed interviews using a separate AI agent
- Persists everything: transcripts, scores, evaluations, code submissions
- Supports interview resumption on WebSocket reconnect

**Does NOT:**
- Does NOT deploy to production (deploy step is a placeholder)
- Does NOT enforce billing (Stripe routes are stubs; free-tier limit is hardcoded at 10 interviews)
- Does NOT run Celery workers in production (Celery is a dependency but unused; APScheduler is used for background eval)
- Does NOT have a dedicated WebSocket server (WebSocket routes live on the same FastAPI process)
- Does NOT use external authentication providers (email/password only)
- Does NOT have granular rate limiting (only basic free-tier cap)

### 1.4 Integration Points

| External Service | Protocol | Purpose | Auth Method | Resiliency |
|-----------------|----------|---------|-------------|------------|
| OpenAI / OpenRouter | HTTPS REST | AI interviewer + evaluator | API key in header | 3 retries with exponential backoff + circuit breaker |
| Deepgram | WebSocket / REST | Speech-to-text | API key | No retry visible in code |
| Resend | HTTPS REST | Transactional email | API key | No retry |
| Stripe | HTTPS REST | Billing (stubbed) | API key | N/A (not implemented) |
| PostgreSQL | asyncpg | Primary database | Connection string | connection pool (10/20) + pool_pre_ping |
| Redis | redis-py | Cache / broker | URL | No explicit HA config |

---

## 2. Core Abstractions & Data Model

### 2.1 Key Entities & Relationships

```
User (users)
  │
  ├── Interview (interviews) ─── InterviewConfiguration (snapshot)
  │     ├── Session events (session_events)
  │     ├── Evaluation (evaluations, 1:1)
  │     ├── Resume (resumes, FK)
  │     └── JobDescription (job_descriptions, FK)
  │
  ├── Subscription (subscriptions, 1:1)
  ├── BillingEvent (billing_events)
  └── UserTemplate (user_templates)
```

**8 migration files** reflect an iterative schema design. Key design choices:

- **`InterviewConfiguration` is denormalized**: When a user completes the setup wizard, the entire configuration is snapshotted into a separate table. This decouples the interview from the mutable wizard state — changing a template or config doesn't retroactively alter past interviews.
- **`Evaluation` is 1:1 with `Interview`**: The `interview_id` column has a unique constraint. This means re-evaluation must delete-and-reinsert rather than upsert. The `EvaluationPipeline` is the single write path (`repository.py:create_evaluation()`).
- **Scores are stored on a 0-5 scale** in the database but displayed as 0-100 in the frontend via `Math.round((score / 5) * 100)`. This conversion exists in multiple components (`StatsGrid`, `InterviewProgress`, `RecentActivityList`). Any new score display MUST use the same formula.
- **`transcript` and `ai_messages` are JSONB columns** on the interview — not separate child tables. For current scale this is fine, but querying transcripts individually (e.g., "find all interviews where the candidate mentioned X") would require a JSONB index or migration to a normalized table.

### 2.2 Session State Machine

```
     ┌─────────┐
     │  IDLE   │
     └────┬────┘
          │ prepare()
          ▼
     ┌──────────┐
     │ PREPARING │
     └────┬──────┘
          │ start()
          ▼
     ┌────────┐  pause()  ┌────────┐
     │ ACTIVE │◄─────────►│ PAUSED │
     └────┬───┘  resume() └────────┘
          │
          ├── complete() ────► COMPLETING ──► COMPLETED
          ├── fail() ────────► FAILED
          └── timeout() ─────► TIMEOUT
```

Defined in `ai/realtime/state_machine.py` with `STATE_TRANSITIONS` dict and `TransitionGuard` for precondition checks. Helper utilities: `is_terminal()`, `is_active()`, `needs_recovery()`.

**Critical detail**: The state machine is in-memory only (Python dataclass). Session state survives process restart only if persisted via `snapshot()` → database. The `features/sessions/` module handles persistence of `Session` dataclass fields.

### 2.3 Database Schema Rationale

- **`pool_size=10, max_overflow=20`**: Tuned for a single-process FastAPI instance. At higher concurrency, these values need adjustment or PgBouncer must be introduced.
- **`pool_recycle=300`**: 5-minute recycle for PostgreSQL's `statement_timeout` and connection lifecycle. Matches common cloud PostgreSQL idle timeout.
- **No explicit indexes beyond PKs and FK columns**: The migration files don't add covering indexes for common queries (e.g., `WHERE user_id = ? ORDER BY created_at DESC`). These are implicitly handled by PostgreSQL's PK-B-tree for UUIDs on `created_at` ordering, but at scale, composite indexes on `(user_id, created_at)` would improve dashboard queries.
- **`deleted_at` columns for soft delete**: `User` and `Interview` use nullable `deleted_at` for soft delete. Queries must include `WHERE deleted_at IS NULL` — this is NOT enforced by a SQLAlchemy filter parameter or a `@where` clause. It's the responsibility of each repository/service to add the filter.

### 2.4 Caching Strategy

There is **no explicit caching layer** beyond PostgreSQL's buffer cache. Key implications:

- Dashboard stats (`GET /dashboard`) queries real-time aggregates every request. At scale, this should be cached in Redis with a 30s TTL.
- The `.env.example` has `REDIS_URL` but Redis is only used for the APScheduler job store and as a dependency for Celery. No application-level caching is implemented.
- The frontend uses `@tanstack/react-query` with `staleTime: 30_000` (30s) for dashboard and `staleTime: 15_000` (15s) for recent interviews. This provides basic client-side caching but no server-side cache invalidation.

---

## 3. API & Interface Contracts

### 3.1 REST API Surface

All routes mount under `http://localhost:8000/api/v1/` except health (`/health`). The `main.py` registers **12 routers**. Response format is standardized via `success_response()`:

```json
{
  "success": true,
  "data": { ... },
  "request_id": "uuid"
}
```

Error format:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "...",
    "details": [...]
  },
  "request_id": "uuid"
}
```

**Full route table:**

| Method | Path | Feature | Auth |
|--------|------|---------|------|
| POST | `/auth/signup` | Register + auto-login | No |
| POST | `/auth/login` | Login | No |
| POST | `/auth/logout` | Revoke refresh token | Yes |
| POST | `/auth/refresh` | Rotate tokens | No¹ |
| POST | `/auth/forgot-password` | Send reset email | No |
| POST | `/auth/reset-password` | Complete reset | No² |
| POST | `/auth/verify-email` | Verify via token | No² |
| GET | `/users/me` | Current user profile | Yes |
| GET/POST/PATCH | `/interviews/*` | Interview CRUD + setup | Yes |
| GET/POST | `/evaluations/*` | Evaluation CRUD | Yes |
| POST | `/evaluations/{id}` | Trigger evaluation | Yes |
| GET | `/dashboard` | Aggregated stats | Yes |
| GET | `/dashboard/recent` | Recent activity | Yes |
| POST/PATCH | `/code/*` | Code submissions + review | Yes |
| POST | `/billing/*` | Stripe stubs | Yes |
| GET | `/health` | Health check | No |
| GET | `/analytics/*` | Usage analytics | Yes |
| POST | `/voice/transcribe` | Deepgram transcription | Yes |

¹ Refresh uses the refresh_token in the request body, not Bearer auth.
² Reset/verify endpoints use the token in the request body, not Bearer auth.

### 3.2 Authentication & Authorization

**Auth flow:**
1. `POST /auth/signup` or `POST /auth/login` returns `{ access_token, refresh_token, user }`
2. `access_token` is a JWT (RS256 in production, HS256 in dev) with 24h expiry
3. `refresh_token` is a separate JWT with 7-day expiry, supporting rotation (old revoked, new issued with same `token_family`)
4. The frontend stores the refresh token in `localStorage` under key `tayari_refresh_token`
5. `access_token` is kept in React state (not localStorage) — it survives page load by calling `/auth/refresh` on mount using the stored refresh token

**Guard chain** (`features/auth/guard.py`):
- `get_current_user` — required auth, returns `CurrentUser` or 401/403
- `get_optional_user` — optional auth, returns `CurrentUser | None` (no error on missing token)
- `RoleChecker("admin")` — decorator returns 403 if user lacks required roles
- `PermissionChecker("users:read")` — decorator returns 403 if user lacks required permissions

**Admin detection**: Hardcoded in `services.py` — email `admin@tayari.ai` gets roles `["admin", "user"]` and permissions `["users:read", "users:write", "users:delete"]`. This is a hardcoded frozenset, not database-driven.

**Token blacklist**: `MemoryBlacklist` — in-memory dict. Does NOT survive process restart. At scale, this must be replaced with a Redis-backed blacklist.

### 3.3 Rate Limiting & Quotas

- **Free-tier cap**: 10 interviews per user, enforced in `features/interview/service.py`. Checked on interview creation.
- **AI cost cap**: `AI_COST_CAP_DOLLARS = 0.30` per interview, enforced via `AI_MAX_TOKENS_PER_INTERVIEW = 10000` (soft limit — no hard enforcement visible).
- **No rate limiting middleware**: No `slowapi`, no Redis-based rate limiter. At production scale, add middleware-based rate limiting per-user and per-IP.

### 3.4 Backward Compatibility

- **No API versioning**: All routes are at `/api/v1/` but there's no version negotiation. Breaking changes would require a new prefix.
- **JWT token types**: Token validation includes a `type` claim (`access`, `refresh`, `email_verify`, `password_reset`). Each endpoint validates the specific type. This prevents token misuse (e.g., using a reset token as an access token).

### 3.5 Event Schemas

**WebSocket protocol** (`session-client.ts` ↔ `ai/realtime/`):

All WebSocket messages are JSON with this envelope:
```json
{
  "type": "event_type",
  "payload": { ... }
}
```

**Client→Server events:**
- `session.join` — join session (with `reconnect` flag + `last_sequence` for resumption)
- `user.answer` — submit answer text
- `user.code` — submit code update
- `session.pause` / `session.resume`
- `session.request_hint`
- `session.end`
- `session.ping` — heartbeat

**Server→Client events:**
- `session.connected` — initial state + remaining time
- `ai.question` — new question from AI interviewer
- `ai.hint` — hint response
- `ai.stream_start` / `ai.token*` / `ai.stream_end` — token streaming
- `session.paused` / `session.resumed` / `session.completing` / `session.completed`
- `timer.tick` / `timer.warning`
- `session.reconnected` — acknowledgement of reconnect

---

## 4. Operational Concerns

### 4.1 Runbook: 3 Most Likely Failure Modes

#### Failure Mode 1: AI Provider Returns Errors (OpenAI/OpenRouter down or rate-limited)

**Symptoms:**
- `ai.failed` events in session logs (`structured_log.py` correlation ID)
- Users report "AI is not responding" or stuck at "Thinking..."
- `AI_LATENCY_HIGH` events from `telemetry.py`

**Diagnosis:**
```bash
curl -s https://api.openai.com/v1/models | jq '.data | length'
# If this fails, the provider is unavailable
```

**Mitigation:**
1. The `RetryPolicy` auto-retries 3 times with exponential backoff (1s base, 15s max, jitter). Failures within these retries are transparent to the user.
2. If retries are exhausted, the session state machine transitions to `FAILED` (not `COMPLETED`). The interview is salvageable — restart the session.
3. For prolonged outages, switch to `MockProvider` by changing the `ai/provider.py` import or env var.

**Recovery:**
- Failed sessions can be retried via `POST /evaluations/{interview_id}` — but the interview transcript must be intact.
- If the AI crashed mid-interview, the session can be resumed (WebSocket reconnect with `reconnect: true, last_sequence: N`).

#### Failure Mode 2: Database Connection Pool Exhaustion

**Symptoms:**
- `SQLAlchemyError` exceptions in logs
- `psycopg2.OperationalError: FATAL: remaining connection slots are reserved`
- Slow responses on any REST endpoint

**Diagnosis:**
```sql
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
SELECT count(*) FROM pg_stat_activity;
-- Compare to pool_size=10 + max_overflow=20 = 30 max
```

**Root causes:**
- Long-running queries blocking connections (check `pg_stat_activity.wait_event`)
- Connection leaks (the `get_db()` dependency has a `finally: await session.close()` which should prevent this)
- Burst traffic exceeding 30 concurrent connections

**Mitigation:**
1. Immediate: reduce `max_overflow` to 10 to avoid overloading the DB.
2. Short-term: Add PgBouncer as a connection pooler in `infrastructure/docker-compose.yml`.
3. Long-term: Monitor `pool_size` and `overflow` usage with a custom metric.

#### Failure Mode 3: WebSocket Disconnection Mid-Interview

**Symptoms:**
- Frontend shows "Reconnecting..." overlay with attempt counter
- `session.reconnected` events in logs
- `heartbeat.missed` events if heartbeats are lost (`HeartbeatMonitor`)

**Mechanism:**
1. Frontend detects WebSocket close → sets `connectionStatus: "disconnected"`
2. `SessionClient` starts exponential backoff with ±30% jitter (max 10 attempts)
3. On reconnect, sends `{ type: "session.join", payload: { reconnect: true, last_sequence: N } }`
4. Backend replays the current question + session state from `SessionManager.snapshot()`

**DANGER:**
If the FastAPI process restarts, ALL in-memory sessions are lost (`SessionManager` is a dict). The frontend's reconnect will fail because the session no longer exists in memory. Session state IS persisted to the database (via `features/sessions/service.py`), but `SessionManager` doesn't reload from DB on startup. Any interrupted session during a deployment is unrecoverable.

### 4.2 Monitoring

**What exists:**
- **Structured logging**: `StructuredLogger` wraps Python logger with `correlation_id` and `session_id` via `ContextVar`. Every log entry includes these. Logs go to stdout.
- **Performance telemetry**: `PerformanceTelemetry` tracks per-session AI latency, transcript latency, total turn time. `session_ended()` returns aggregated metrics. Not exported to any external system.
- **Audit logging**: `AuditLogger` emits structured JSON to the `"auth.audit"` logger for auth events (login, register, password reset, email verify). Logs include `email_hash` (SHA-256 prefix, 16 chars), not raw email.
- **Sentry**: `sentry-sdk` is a dependency but does NOT appear to be initialized in `main.py` or `core/config.py`.

**What's missing:**
- No metrics endpoint (`/metrics` for Prometheus)
- No health check beyond a simple `GET /health` (doesn't verify DB/Redis connectivity)
- No alerting rules
- No request duration histograms
- No connection pool utilization metrics

### 4.3 Deployment Process

**Current state:**
1. CI (`ci.yml`) runs on push/PR to `main` or `feature/**`:
   - Lint & TypeCheck (ruff + mypy + eslint + tsc)
   - JS Tests (vitest)
   - Python Tests (pytest with Postgres + Redis services)
   - Build (next build + perf budget check)
2. Docker CI (`docker.yml`) runs on PR/merge to `main`:
   - Builds `tayari-api` and `tayari-web` Docker images (no push to registry)
3. Deploy step is a **placeholder** — prints supported targets, does nothing.

**Canary strategy**: None. There are no staging/production environments, no feature flags at the infrastructure level (only frontend feature flags like `NEXT_PUBLIC_FF_BILLING`), and no blue-green deployment.

**Rollback procedure**: None. Would require `git revert` + re-push.

### 4.4 Capacity Planning

**Current bottlenecks:**

| Resource | Current | Limit | Cliff |
|----------|---------|-------|-------|
| DB connections | 10 pool + 20 overflow | PostgreSQL default (100) | Higher traffic requires PgBouncer |
| AI tokens | 10K tokens/interview | $0.30 cost cap | Cost grows linearly with users |
| In-memory sessions | Unlimited (dict) | RAM | Process restart loses all sessions |
| WebSocket per process | Unlimited | Uvicorn workers (1) | Single worker = one WebSocket at a time per connection |

**Scaling limits:**
- The monolith FastAPI process will be the first bottleneck. WebSocket sessions share the same event loop as REST handlers. At ~100 concurrent interview sessions, AI streaming latency will impact REST response times.
- `pool_size=10` limits concurrent DB operations to 10. The `max_overflow=20` provides burst but risks `FATAL: too many connections` on PostgreSQL default config.

### 4.5 Data Retention, Backup, and DR

- **No backup strategy defined**: No automated backups, no WAL archiving, no replication.
- **Soft deletion**: Users and interviews have `deleted_at` columns. Hard deletion is NOT implemented anywhere.
- **Transcript storage**: `transcript` and `ai_messages` are JSONB on the interview row. At scale, archive transcripts to S3-compatible storage (the config already has `STORAGE_BUCKET`, `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY` — but no code uses them).
- **No disaster recovery plan**: No cross-region replication, no backup restore procedure.

---

## 5. Design Decisions & Trade-offs (ADRs)

### ADR 1: In-Memory Session Manager vs. Database-Backed Sessions

**Decision**: Session state lives in a Python `dict[SessionId, Session]`. Snapshots are persisted to the database on state transitions.

**Why**: Interview sessions require low-latency state transitions (every turn involves AI streaming, transcript updates, heartbeat checks). A database round-trip per state change would add 5-15ms of latency to a process already waiting 500-3000ms for AI responses. The in-memory approach keeps turn latency sub-millisecond for the state machine itself.

**Trade-off**: Process restart destroys all active sessions. The frontend's reconnect mechanism returns a 404 because the session no longer exists in memory. Mitigation requires either:
1. Loading active sessions from the database on startup (not implemented)
2. Session affinity via sticky WebSocket routing (requires a load balancer)
3. Externalizing session state to Redis (defeats the latency advantage)

**When this breaks**: During any deployment that restarts the API process. All active interviews are lost.

### ADR 2: Feature-First Module Structure vs. Layer-First (MVC)

**Decision**: Each feature is a self-contained package with its own `routes.py`, `service.py`, `repository.py`, `schemas.py`, `dependencies.py`, and `tests/`.

```python
# Example: features/auth/ contains EVERYTHING for auth
features/auth/
  routes.py      # FastAPI router
  services.py    # Business logic
  repositories.py # Data access
  schemas.py     # Pydantic request/response models
  guard.py       # Auth guards (get_current_user, etc.)
  dependencies.py # DI wiring
  domain/        # Domain models
  jwt/           # JWT sub-module
  password/      # Password hashing sub-module
```

**Why**: This is the "inside-out" pattern advocated by FastAPI's documentation and production FastAPI projects. It enables:
- Feature teams to work independently without merge conflicts in a shared `routes/` or `models/` file
- Easy feature flagging / toggling at the router registration level
- Clear ownership boundaries

**Trade-off**: Cross-feature dependencies require explicit imports between feature packages. The `reports/` service imports from `interview/` (to load interview data). This creates a implicit coupling graph. A circular import between features would be caught at import time due to Python's import system, but a layered architecture (interfaces in a shared package) would make the dependency graph explicit.

### ADR 3: JWT with HS256 Default, RS256 Override

**Decision**: `JWTConfig` defaults to HS256, but `core.config.Settings` overrides to RS256 for production. The `dependencies.py` comment explains this.

```python
class JWTConfig:
    ALGORITHM: str = "HS256"  # Overridden by Settings.JWT_ALGORITHM
```

**Why**: HS256 (symmetric) is simpler for development — no key pair management. RS256 (asymmetric) is required for production to enable separate signing (API) and verification (potentially other services) without sharing secrets.

**Trade-off**: The `JWT_SECRET_KEY` serves double duty. In HS256 mode, it's the HMAC secret. In RS256 mode, it's expected to be a PEM-encoded RSA private key. The config doesn't differentiate. If `JWT_ALGORITHM=RS256` but `JWT_SECRET_KEY` is a plain string (not a PEM key), token creation will fail with a cryptic `python-jose` error.

### ADR 4: APScheduler over Celery for Background Tasks

**Decision**: Background evaluations use APScheduler with a `SQLAlchemyJobStore` instead of Celery.

**Why**: Celery was added as a dependency (listed in `pyproject.toml`) but never wired. APScheduler is simpler for the current single-process deployment:
- No broker required (uses PostgreSQL for job persistence)
- The `schedule_evaluation()` function is synchronous and runs in-process with `AsyncIOExecutor`
- Job deduplication is handled by removing existing jobs for the same interview_id

**Trade-off**: APScheduler runs in the same process as the web server. A CPU-intensive evaluation blocks the event loop, impacting REST and WebSocket latency. The `max_instances=3` limits concurrent evaluations, but each evaluation calls `gpt-4o` (structured output), which is I/O-bound (network wait), not CPU-bound. The real risk is memory pressure if multiple evaluations run concurrently.

**When this breaks**: If the API process restarts, pending evaluation jobs are preserved in PostgreSQL (SQLAlchemyJobStore survives restarts). However, there's no mechanism to ensure a crashed evaluation is retried — the job store only preserves the schedule, not in-flight work.

### ADR 5: Score Normalization (0-5 vs. 0-100)

**Decision**: All scores are stored as 0-5 (float) in the database. Frontend converts to 0-100 for display using `Math.round((score / 5) * 100)`.

**Why**: AI model outputs (structured evaluation) naturally produce 0-5 scores. Storing the raw value avoids precision loss from rounding. The conversion happens at the presentation layer.

**Trade-off**: The conversion formula is duplicated in 6+ frontend components (`StatsGrid`, `InterviewProgress`, `RecentActivityList`, `EvaluationDashboard`, `ScoreCard`, etc.). There's no shared utility function, so each component independently implements `Math.round((score / 5) * 100)`. This is a normalization drift risk — a future developer might use `(score / 5) * 100` without `Math.round`, producing scores like `87.99999999999999%`.

**WARNING**: Never pass a 0-100 value into these components. If the value is already a percentage (e.g., from a new API endpoint), the conversion will double-apply and produce incorrect results like `1700%` (as seen in a prior test failure where `average_score: 85` was treated as 0-5 scale, resulting in `Math.round((85/5)*100) = 1700`).

---

## 6. Security & Compliance

### 6.1 Threat Model Summary

| Threat | Mitigation | Gap |
|--------|-----------|-----|
| JWT token theft | Short TTL (24h access, 7d refresh), refresh token rotation | `MemoryBlacklist` doesn't survive restart |
| SQL injection | SQLAlchemy ORM (parameterized queries everywhere) | Raw SQL in Alembic migrations is safe but unenforced |
| XSS via interview content | React 19 auto-escaping | No CSP reporting endpoint |
| CSRF | SameSite cookie not used (Bearer token in header) | No CSRF tokens needed with Bearer auth |
| Enumeration via forgot-password | Always returns 200 regardless of email existence | Standard practice |
| Email leak in audit logs | `email_hash` is SHA-256 prefix (16 chars) | Brute-forceable for common email domains |
| Password brute force | bcrypt with 12 rounds | No account lockout or rate limiting on login |

### 6.2 Secrets Management

- **`.env` files committed to repo**: `apps/api/.env` contains a real Deepgram API key and OpenRouter API key. These were committed at some point and are visible in git history.
- **No secret rotation mechanism**: JWT secret, API keys are static.
- **No encryption at rest for secrets**: Plaintext in `.env` files.
- **`JWT_SECRET_KEY` in CI**: Set as `test-secret-key` environment variable in `ci.yml` — acceptable for CI, but the same CI runs Python tests that connect to a real PostgreSQL and Redis instance.

### 6.3 Data Classification

| Data | Classification | Storage | Notes |
|------|---------------|---------|-------|
| Email | PII | `users.email` | Unique index, encrypted at rest (PostgreSQL) |
| Password hash | Secrets | `users.password_hash` | bcrypt (12 rounds), never logged |
| Interview transcripts | User content | `interviews.transcript` (JSONB) | Unencrypted in DB |
| AI evaluation text | Generated content | `evaluations.raw_evaluation` (Text) | Could contain resume data |
| Resumes | PII + User content | `resumes.storage_path` | File stored in S3-compatible bucket (not implemented) |
| Deepgram audio | User content | Not persisted (streamed) | Never stored |

### 6.4 Audit Logging

- **Auth events only**: Login, register, logout, token refresh, password reset, email verification.
- **`email_hash`**: SHA-256 of the email, truncated to 16 hex characters. Example: `a1b2c3d4e5f6g789`. This provides partial anonymity but is reversible for common email addresses via rainbow tables on the first 64 bits.
- **Audit format**: JSON lines to `"auth.audit"` logger (stdout by default). No dedicated log sink.

---

## 7. Development & Testing

### 7.1 Local Setup

```bash
# Prerequisites: Python 3.13+, Node.js 22+, pnpm 9+, Docker (for Postgres/Redis)

# 1. Start infrastructure
docker compose -f infrastructure/docker-compose.yml up -d db redis

# 2. Install Python deps (API)
cd apps/api
uv sync --all-extras          # installs ruff, mypy, pytest, etc.
uv run alembic upgrade head   # run migrations
uv run python scripts/seed.py # seed interview templates

# 3. Install JS deps (root monorepo)
cd ../..                      # back to root
pnpm install                  # installs all workspaces

# 4. Start development
pnpm dev                      # turbo dev — starts API + Web concurrently
```

**NOTE**: The API's `pnpm dev` script is `uv run uvicorn main:app --reload`. This requires `uv` to be installed and accessible. The `--reload` flag watches for Python file changes but does NOT detect new dependency installations — restart manually after `uv sync`.

**Local gotchas:**
- The pre-commit hook runs `ruff check --fix` + `ruff format` on staged Python files. If these modify your files, `git add` them again before the final commit.
- Pre-commit also runs `pytest tests/` with `--quiet -x` against your local database. If PostgreSQL isn't running, the commit blocks until you Ctrl+C or start Postgres.
- The `.husky/pre-commit` script suppresses `stderr` for the test command (`2>/dev/null`). Test failures print a warning but the exit code still aborts the commit.
- Ruff and mypy are installed via `uv sync --all-extras`, not globally. They must be run through `uv run` or via the scripts in `package.json` (which now use `uv run`).

### 7.2 Test Pyramid

| Layer | Tool | Location | What's Tested | What's Mocked |
|-------|------|----------|---------------|---------------|
| Unit (frontend) | Vitest + React Testing Library | `apps/web/__tests__/` | Component rendering, state logic, error/loading/empty states | `useRouter`, `useAuth`, API calls |
| Unit (backend) | Pytest + pytest-asyncio | `apps/api/tests/`, `apps/api/features/*/tests/` | Auth validation, session guards, email service | Database (test schema), AI providers |
| Integration | Pytest + live DB | `apps/api/tests/` | Full request→DB→response for auth endpoints | External services (AI, email) |
| E2E | Not implemented | `apps/api/tests/test_e2e_evaluation.py` | — | — |

**Current counts**: 437+ Python tests, 92 JS tests. E2E tests are excluded from CI (`--ignore=tests/test_e2e_evaluation.py`).

**Coverage gaps:**
- No tests for `ai/realtime/` (state machine, orchestrator, session manager)
- No tests for `workers/` (scheduler, evaluation worker)
- No tests for WebSocket routes (`features/sessions/routes.py`)
- 2 pre-existing test failures in the `WebSocket` event tests
- The `ai/tests.py` and `features/billing/tests.py` files are placeholders

**Testing patterns:**
- Backend uses `httpx.AsyncClient` for integration tests (mounted FastAPI app — no real server needed)
- Database tests use a test PostgreSQL instance (spawned by CI via Docker service)
- Frontend uses `vitest` with `jsdom` environment
- `test_auth.py` tests validation: email format, password length, username constraints
- `test_sessions.py` tests auth guards: unauthenticated requests return 401
- `test_email_service.py` tests HTML generation (URLs embedded, copy checks) and API key guard logic

### 7.3 CI/CD Pipeline

```
Push to feature/** or main
         │
         ▼
    ┌─────────────────────────────────────────────┐
    │             lint-and-typecheck               │
    │  ruff check .  │  eslint .  │  mypy .  │ tsc │
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │                js-tests                      │
    │      pnpm --filter @tayari/web test          │
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │              python-tests                    │
    │  pytest (Postgres 17 + Redis 7 containers)  │
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │                  build                       │
    │   next build  +  performance-budget.mjs     │
    └──────────────────────┬──────────────────────┘
                           │ (main + push only)
                    ┌──────▼──────┐
                    │   deploy    │
                    │ (placeholder)│
                    └─────────────┘
```

**Concurrency**: CI uses `concurrency.group: ${{ github.ref }}` with `cancel-in-progress: true`. Push to a branch cancels the previous run.

**Turbo caching**: CI caches `.turbo` directories between runs. Cache key is `pnpm-lock.yaml` hash. If the lockfile doesn't change, turbo replays cached task outputs. This means lint errors might not surface if a previous successful lint was cached. **Disabled remote caching** — only local GitHub Actions cache.

### 7.4 Pre-commit Hooks & Linting

**Hook chain** (`.husky/pre-commit`):
1. `lint-staged`:
   - `*.{ts,tsx,js,jsx,json,md}` → `prettier --write`
   - `*.py` → `ruff check --fix` + `ruff format`
2. If Python files changed → `uv run pytest tests/ --ignore=tests/test_e2e_evaluation.py --quiet --tb=short -x`

**Ruff config** (`pyproject.toml`):
- Rules: E, F, I, N, W, UP
- Line length: 120
- Per-file ignores: `alembic/**` (E501), `judge/**` (E501, E741, E402), `ai/mock_provider.py` (E501)
- Target: py313

**ESLint config** (`apps/web/eslint.config.js`):
- Extends `@tayari/config/eslint/base.js` (no-unused-vars as warn, no-console as warn, prefer-const, no-var)
- Adds `@next/next` plugin with recommended + core-web-vitals rules
- Custom globals for `public/audio-processor.js` (AudioWorkletProcessor, registerProcessor, sampleRate) and `scripts/performance-budget.mjs` (console, process)

**Prettier**: Single quotes, trailing commas, 100 print width, LF line endings.

---

## 8. Known Issues & Technical Debt

### 8.1 Critical Code Smells

1. **`MemoryBlacklist` for JWT revocation** (`features/auth/jwt/jti_blacklist.py`): An in-memory dict means:
   - Token revocation is lost on restart
   - Multi-process deployments have inconsistent blacklists
   - No expiry-driven cleanup (prunes on check, but leaked entries consume memory)
   - **Fix**: Replace with Redis-backed blacklist before production.

2. **`SessionManager` stores sessions in memory** (`ai/realtime/session_manager.py`):
   - Process restart kills all active interviews
   - No reload from database on startup
   - Single-process only — doesn't work with multiple Uvicorn workers
   - The snapshot/restore mechanism exists but `restore()` is never called on startup

3. **Hardcoded admin email** (`features/auth/services.py:17`):
   ```python
   _ADMIN_EMAILS = frozenset({"admin@tayari.ai"})
   ```
   - Not configurable via environment variable
   - Only checked on registration — changing it later doesn't retroactively grant admin
   - **Fix**: Move to database-driven roles or env config.

4. **Unused Celery dependency**: Celery 5.6 is listed in `pyproject.toml` dependencies but never used. APScheduler handles background tasks. Celery adds ~500KB to the deployment image and introduces `billiard`, `kombu`, `amqp` transitive dependencies for nothing.

5. **`uv sync` without `--all-extras` breaks CI** (resolved in commit `37028e4`): The CI was failing because `ruff`, `mypy`, and `pytest` are in `[project.optional-dependencies.dev]` which wasn't installed by `uv sync`. The fix was to:
   - Remove the `[dependency-groups]` section (which shadowed `[project.optional-dependencies.dev]` in uv ≥0.5)
   - Add `--all-extras` to all `uv sync` commands in CI
   - Prefix all `package.json` scripts with `uv run`
   
   **NOTE**: This means ALL API scripts now depend on `uv` being at the project root. Running `ruff check .` directly without `uv run` will fail if ruff isn't globally installed.

### 8.2 Race Conditions

- **Concurrent interview creation**: The free-tier check (`interview_count < 10`) is subject to a TOCTOU race condition. Two concurrent requests could both check and find 9 interviews, then both create interview #10. Fix: Use a database-level constraint or `SELECT ... FOR UPDATE`.
- **Refresh token rotation**: The `revoke_family` method invalidates all tokens in a family before issuing a new one. If two concurrent requests try to refresh using the same token, the second one's old token is already revoked and fails. This is intentional (detected replay attack), but the error message is opaque: "Token already revoked."
- **Schedule evaluation duplicate**: The scheduler removes existing jobs for the same `interview_id` before scheduling a new one (`workers/scheduler.py`). However, between the removal and the insert, another process could schedule the same evaluation.

### 8.3 Deprecated / Scheduled for Removal

- **`features/billing/`**: All 4 endpoints return JSON stubs saying "Not implemented." The Stripe integration is not wired. Routes exist behind `/api/v1/billing/` and are registered in `main.py`. They respond with 200 but no actual functionality. If Stripe is never coming, remove the routes.
- **`ai/tests.py`, `features/billing/tests.py`, `features/reports/tests.py`**: These are placeholder files with empty test classes or pass statements. They were likely created with the feature scaffold and never removed.
- **`core/dependencies.py`**: Contains a simpler legacy `get_current_user` implementation that uses `HTTPBearer` and a separate `decode_jwt` function. The newer auth guard in `features/auth/guard.py` is the primary mechanism. This legacy dependency is likely unused.

### 8.4 Performance Hotspots

1. **Dashboard aggregate queries**: `GET /dashboard` computes aggregates (count, average, streak) in real time. On the `interviews` table (which uses a UUID PK), `COUNT(*) WHERE user_id = ?` requires a sequential scan if no index exists on `user_id`. The `interviews.user_id` FK likely has an index (Alembic typically creates FK indexes), but this should be verified.

2. **Evaluation pipeline**: `POST /evaluations/{interview_id}` loads the full interview (including JSONB `transcript` and `ai_messages`), sends the entire transcript to `gpt-4o` for evaluation, then writes the result. For long interviews (30+ questions), the transcript could be 50K+ tokens. The evaluation uses `gpt-4o` (not `gpt-4o-mini`), which is more expensive and slower. The `AI_EVALUATOR_MODEL` config setting controls this.

3. **WebSocket + REST on the same event loop**: Single Uvicorn worker means all WebSocket connections and REST requests share the same asyncio event loop. A slow AI response or a stalled database query blocks everything. At scale, separate the WebSocket handler into its own process.

4. **JSONB queries without indexes**: `interviews.transcript` and `interviews.ai_messages` are JSONB columns with no GIN indexes. Queries like `WHERE transcript @> '{"speaker": "user"}'` would require a full table scan.

---

## 9. Glossary

| Term | Definition |
|------|-----------|
| **APScheduler** | Advanced Python Scheduler — in-process task scheduler with SQLAlchemyJobStore (PostgreSQL) for persisted job scheduling. Used for background evaluation. |
| **Behavioral interview** | Interview type focusing on past experience, leadership, conflict resolution, using STAR method. Prompts in `packages/prompts/interviewers/behavioral.md`. |
| **Coding interview** | Interview type focusing on algorithmic problem-solving with live code editor (Monaco). Prompts in `packages/prompts/interviewers/coding.md`. |
| **Correlation ID** | UUID attached to every log entry via ContextVar, enabling request tracing across the stack. |
| **CurrentUser** | Pydantic model from `features/auth/guard.py` containing id, email, roles, permissions. The standard auth dependency for protected routes. |
| **Deepgram** | External STT (speech-to-text) service. Integrated via `features/voice/deepgram_service.py`. Model: `nova-3`, endpointing: 300ms (configurable). |
| **Evaluation Pipeline** | The process of running a completed interview transcript through `gpt-4o` with structured output to produce scores, verdict, and feedback. |
| **Hire verdict** | Categorical outcome: `strong_hire`, `hire`, `lean_hire`, `lean_no_hire`, `no_hire`. Stored as string in evaluations table. |
| **JWT family** | A group of related refresh tokens. When a new refresh token is issued (rotation), all tokens in the same family are revoked. Detects token reuse. |
| **MemoryBlacklist** | In-memory JWT blacklist (dict). Does not survive restart. Will be replaced by Redis. |
| **Monorepo** | pnpm workspace with 6 packages: `@tayari/api`, `@tayari/web`, `@tayari/types`, `@tayari/prompts`, `@tayari/config`, `@tayari/ui`. |
| **Orchestrator** | `AIOrchestrator` in `ai/realtime/orchestrator.py` — manages the AI turn loop: generate question → wait for answer → generate next question or wrap up. |
| **OpenRouter** | The current AI provider endpoint (configured via `OPENAI_BASE_URL`). Routes requests to multiple model providers. Used instead of direct OpenAI API. |
| **Resend** | Email delivery service. `RESEND_API_KEY` in config. Used for password reset and email verification. |
| **Session resumption** | WebSocket reconnect mechanism. Frontend sends `reconnect: true` + `last_sequence`. Backend replays current question + state. Up to 10 reconnection attempts. |
| **STAR** | Situation, Task, Action, Result — structured answer format for behavioral questions. |
| **System-design interview** | Interview type focusing on architecture, trade-offs, scaling. Uses whiteboard component. Prompts in `packages/prompts/interviewers/system-design.md`. |
| **Token rotation** | On refresh, the old token is revoked and a new token with the same `token_family` is issued. This limits the window for token replay. |
| **Turbo** | Turborepo task orchestrator. Runs tasks across packages with caching. Caches lint, build, and typecheck outputs. |
| **uv** | Fast Python package manager (Rust). Replaces pip/poetry. Uses `uv.lock` for deterministic installs. |
| **WidgetErrorBoundary** | React error boundary pattern wrapping individual dashboard widgets. Prevents one widget's crash from taking down the entire dashboard. |
