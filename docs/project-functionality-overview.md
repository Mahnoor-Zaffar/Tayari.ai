# Tayari.ai — Project Functionality Overview

> Principal-engineer onboarding review of the existing codebase. This document
> describes how the system **actually** works, based on direct inspection of the
> implementation (commit `41503a2`, branch `main`), not just the design
> documentation. Where documentation and implementation disagree, the
> implementation reality is documented and the discrepancy is flagged.
>
> Scope reviewed: `apps/api` (FastAPI), `apps/web` (Next.js 15), `packages/`,
> `infrastructure/`, `.github/workflows/`, Alembic migrations, background
> workers, the realtime engine, and the AI integration layer.

---

## 1. Executive Summary

**Tayari.ai** is a real-time AI mock-interview platform. It simulates technical
interviews across three modalities — behavioral (voice/conversational), coding
(Monaco editor + sandboxed execution), and system-design (canvas whiteboard) —
then produces structured AI evaluations and analytics. It is a client-side SPA
(Next.js) talking to a single FastAPI monolith over REST + WebSockets.

### Primary user journey

1. Register/login (email/password, JWT auth, optional Supabase Google OAuth).
2. Configure an interview in a 4-step wizard (type, preferences, resume/JD uploads, review).
3. Start the interview → WebSocket session with an AI interviewer that asks
   questions, remembers the conversation, streams responses, and (for coding)
   runs the candidate's code in a sandbox.
4. End the session → transcript is persisted; a background APScheduler job runs
   an AI evaluation pipeline that produces a 0–5 structured scorecard.
5. Review the evaluation report and aggregate analytics on the dashboard.

### Major technical capabilities

- **Realtime interview engine**: in-memory session state machine, AI turn loop,
  conversation memory (20-turn sliding window), token streaming, heartbeat,
  reconnection with sequence-based replay.
- **Voice pipeline**: browser AudioWorklet PCM capture → WebSocket proxy →
  Deepgram STT (nova-3) → live partial/final transcripts.
- **Code judge**: Docker-isolated execution (7 languages), async submission
  queue, auto-triggered AI code review.
- **Modular AI evaluation**: type-specific + cross-cutting evaluators, score
  aggregation, structured JSON output.
- **Ops baseline**: Sentry, S3/MinIO storage, Redis-backed JWT blacklist,
  APScheduler with PostgreSQL job store, session restore on restart,
  510 passing Python tests / 92 JS tests.

### Current production-readiness level

**Feature-complete, not launch-ready.** The product surface is ~90% implemented,
but there are two shipping blockers (background evaluation is broken by a
`session_id`/`interview_id` mismatch; billing is entirely stubbed), three
verified security gaps (unauthenticated code execution + both WebSocket
endpoints, path-traversal in storage keys), and no real deployment pipeline
(the CI `deploy` job is a placeholder echo). This is a high-quality
portfolio/development codebase that needs a focused hardening pass before public
release.

---

## 2. System Architecture Overview

### 2.1 High-level architecture

Single-process FastAPI monolith + Next.js SPA. All realtime traffic (interview
sessions, voice) shares the same event loop as REST handlers. State that must be
fast lives in-process; state that must survive restart lives in PostgreSQL.

```
Browser (Next.js 15 / React 19)
  │  REST  (axios-style client + TanStack Query)
  │  WS    (interview sessions, voice proxy)
  ▼
FastAPI (uvicorn, single process)
  ├── Middleware: security headers → request-id → auth audit → CORS
  ├── REST routers (/api/v1/*) — auth, users, interviews, sessions,
  │   code, evaluations/reports, dashboard, analytics, voice, billing(stub)
  ├── WebSocket: /sessions/{id}/ws, /voice/stream
  ├── AI engine (ai/realtime) — orchestrator, state machine, memory
  ├── Evaluation pipeline (evaluation/) + workers/ (APScheduler)
  └── Judge (judge/) — Docker sandbox
        │
        ▼
PostgreSQL 17 (SQLAlchemy async/asyncpg)   Redis 7 (JWT blacklist, APScheduler job store)
MinIO/S3 (resumes, JDs — metadata-only today)
External: OpenAI/OpenRouter (AI), Deepgram (STT), Resend (email), Stripe (stubbed)
```

### 2.2 Frontend/backend communication

- **REST**: all routes under `http://localhost:8000/api/v1/`, standardized
  envelope `{ success, data, request_id }`. Errors are `{ success, error:
  { code, message }, request_id }`. Frontend client at
  `apps/web/lib/api/client.ts` (single-flight 401-refresh queue).
- **WebSocket**: interview sessions at `/api/v1/sessions/{session_id}/ws`;
  voice at `/api/v1/voice/stream`. Message envelope
  `{ "type": "...", "payload": {...} }`.
- The frontend is a client-side app; `app/dashboard/layout.tsx` gates routes by
  auth status client-side (no Next.js middleware).

### 2.3 External service integrations

| Service | Protocol | Purpose | Resiliency |
|---|---|---|---|
| OpenAI / OpenRouter | HTTPS | AI interviewer + evaluator (`gpt-4o-mini` / `gpt-4o`) | retry policy in `ai/realtime/retry_policy.py` |
| Deepgram | WS | STT, model `nova-3`, 300ms endpointing | reconnect + drop detection (fixed `41503a2`) |
| Resend | HTTPS | password reset / email verification | none |
| Stripe | HTTPS | billing — **all stubs return "Not implemented"** | n/a |
| PostgreSQL | asyncpg | primary store | pool 10/20, `pool_pre_ping` |
| Redis | redis-py | JWT blacklist, APScheduler job store | none |

### 2.4 Major system boundaries

- **Feature modules** (`apps/api/features/*`): routes → services → repositories →
  schemas/models. Business logic in services; DB access in repositories; thin
  routes. This is the invariant enforced by `context/AGENTS.md`.
- **AI engine** (`apps/api/ai/realtime/*`): orchestrator, session manager,
  state machine, memory, transcript, prompt builder. Owns the live interview
  turn loop and its in-memory state.
- **Evaluation** (`apps/api/evaluation/*`): reads persisted transcripts, runs
  LLM evaluators, aggregates scores. Deliberately separate from the realtime
  engine; runs in APScheduler worker context.
- **Judge** (`apps/api/judge/*`): code sandboxing + submission queue.
- **Persistence** (`apps/api/core/*`, `features/*/models.py`): SQLAlchemy
  ORM + Alembic migrations.

---

## 3. Application Lifecycle

### 3.1 Authentication

**Registration/login**: `POST /auth/signup` and `POST /auth/login`
(`features/auth/routes.py`) return `{ access_token, refresh_token, user }`.

**Token lifecycle** (`features/auth/jwt/service.py`):
- Typed JWTs with `type` claim: `access` (24h), `refresh` (7d),
  `email_verify` (24h), `password_reset` (1h). All carry `sub, exp, iat, jti,
  iss, aud`; access tokens additionally carry `roles` + `permissions` claims.
- `refresh` tokens carry a `token_family`. On rotation the whole family is
  revoked (`revoke_family`) — replay of a rotated token burns the family
  (replay-detection).
- Revocation backend: **Redis-backed blacklist** (`features/auth/jwt/redis_blacklist.py`)
  when `REDIS_URL` is non-localhost; falls back to `MemoryBlacklist` in dev
  (per `auth/dependencies.py`).

**Authorization checks** (`features/auth/guard.py`):
- `get_current_user`: parses `Bearer`, verifies token type, blacklist, then
  **loads the user from the DB** (user existence + `is_active` checked, so a
  deleted/disabled account is rejected even with a valid token).
- `get_optional_user`: same but returns `None` on any failure.
- `RoleChecker("admin")` / `PermissionChecker("users:delete")`: guard classes
  matching roles/permissions claims from the JWT.

**Admin detection**: granted at registration based on `ADMIN_EMAILS` env
(comma-separated, default `admin@tayari.ai`) — `core/config.py`. Not
database-driven; changing the env var does not retroactively re-role existing
users.

**Session handling (client)**: access token lives in React memory only;
refresh token in `localStorage["tayari_refresh_token"]`
(`apps/web/features/auth/hooks/use-auth.tsx`). On page load the client calls
`/auth/refresh` to re-obtain an access token. Refresh token in `localStorage`
is XSS-stealable — a known hardening gap.

### 3.2 Interview creation

- **Configuration**: 4-step wizard (`features/interview/components/
  InterviewSetupWizard.tsx`): Interview Type → Preferences → Uploads →
  Review. Draft autosaved to `localStorage` with 24h TTL. Options (companies,
  roles, durations, difficulty) come from `GET /interviews/options`.
- **DeviceCheckStep** exists but is **not wired into the wizard** and its
  `/api/health` fetch targets a Next.js route that doesn't exist — dead code.
- **Persistence**: `POST /interview-setup` (`features/interview/service.py`)
  snapshots the config into `interview_configurations` and creates the
  `interviews` row (denormalized snapshot — later template changes don't
  retroactively alter past interviews).
- **Free-tier cap**: `FREE_TIER_INTERVIEW_LIMIT = 10`, enforced in
  `service.py:80` via `count_user_interviews()`. The count filters
  `deleted_at IS NULL`, so soft-deleted interviews don't count. There is a
  TOCTOU race (count-then-insert) with no DB constraint.
- **Resume/JD upload**: `upload_resume` / `upload_job_description` store
  **metadata only** (filename, mime, size, hash) plus a computed
  `storage_path`. The actual file bytes are never written to storage in the
  current implementation — the presigned-URL flow in `core/storage.py` has no
  callers. `get_resume_file` reads from storage, but nothing stores bytes.
  Deduplication is by SHA-256 `file_hash` supplied by the client.
- **Resume parsing / JD analysis are keyword stubs**: `parse_resume` extracts
  technologies from the filename only; `analyze_job_description` does keyword
  matching on raw content. Both return empty `experience`/`requirements` with
  hardcoded confidence values. No AI is involved.

### 3.3 Interview execution

**WebSocket lifecycle** (`features/sessions/routes.py`, `ai/realtime/`):

1. `POST /sessions { interview_id }` → `SessionService.start_session()` loads
   the interview + resume/JD context, creates a `Session` in the in-memory
   `SessionManager`, prepares, and starts it (state → ACTIVE).
2. Client connects `WS /sessions/{id}/ws`, sends `session.join`
   (with `reconnect` flag + `last_sequence` for resumption). Server replays
   current question + state.
3. Server pushes events: `session.connected`, `ai.question`,
   `ai.stream_*` (streaming), `timer.tick`, `session.paused/resumed/completing/completed`.
   Client sends: `user.answer`, `user.code`, `session.pause/resume/request_hint/end`, `heartbeat`.

**AI interviewer orchestration** (`ai/realtime/orchestrator.py`):
- Turn loop: `generate_initial_question()` → stream to client → wait for
  `user.answer` → `process_answer()` appends to memory, generates next question
  → repeat until question limit (`behavioral: max(12, minutes//2)`, others
  `max(6, minutes//5)`), then `generate_wrap_up()`.
- `ConversationMemory` keeps a sliding window of `DEFAULT_MAX_TURNS = 20`,
  pinning the system prompt + context. Older turns are dropped — this bounds
  token cost but means long interviews lose early context.
- Prompt construction: `PromptBuilder` loads Markdown templates from
  `packages/prompts/interviewers/{type}.md`, interpolates config, appends
  company-specific templates, resume context, JD context, and custom
  instructions. **The system prompt is never hardcoded in business logic** —
  templates live in `packages/prompts/` and are loaded by path resolution from
  `apps/api/ai/realtime/` up to the repo root.

**Voice pipeline** (`features/voice/`):
- Browser AudioWorklet (`public/audio-processor.js`) downmixes to mono,
  resamples to 16kHz, converts Float32→Int16, sends 0.5s chunks over
  `WS /voice/stream` as binary frames.
- Server `DeepgramProxy` (`features/voice/deepgram_service.py`) proxies audio
  to Deepgram and forwards partial (`is_final=False`) / final (`is_final=True`)
  / `speech_final` transcript events back to the client.
- Client auto-submits an answer on `speech_final` and auto-starts the mic on a
  new question (`use-deepgram-recognition.ts`). Mic bugs fixed in `41503a2`
  (drop detection, stop-message handling, clipping, transcript buffer cap).

**Conversation memory & transcripts**: the `TranscriptManager` accumulates
segments per question; on session end, `SessionService.end_session()` persists
the transcript into `interviews.transcript` (JSONB) before completing. Memory
snapshots are separate from transcripts.

**Reconnection handling**:
- Client: exponential backoff with ±30% jitter, 10 attempts max
  (`lib/session-client.ts`), heartbeat every 10s.
- Server: on reconnect, replays `session.connected` + current question.
- **Server restart**: `main.py` lifespan now calls
  `SessionRepository.find_active_sessions()` and `manager.restore_sessions()`
  (added post-`dfe47dc`). **However, restored sessions have no orchestrator or
  memory** — `SessionService.process_answer` raises `ValueError` for a session
  with `orchestrator is None`, so a restored session's answers still fail. The
  session is restored in name only. (Verified: `service.py:197`.)

**What the WS server does NOT do**: verify the token or that the connecting
user owns the session. `interview_websocket` calls `websocket.accept()` then
checks only that the session UUID exists in memory. No auth dependency, no
ownership check (docstring claims otherwise). Also note the double
`websocket.accept()` in the not-found branch (`routes.py:179,183`) raises a
`RuntimeError`, so that error path never delivers its message.

### 3.4 Coding interview flow

- Client `CodeSession.tsx` (Monaco, custom theme) persists per-language code
  drafts to `localStorage`; `POST /code/run`, `POST /code/submit`,
  `GET /code/result/{id}` (polled), `GET /code/languages`.
- `CodeExecutionService` enqueues into `judge/queue.py`
  (`ExecutionQueue`, concurrency-throttled via a public
  `concurrency_semaphore`); `judge/sandbox.py` executes in Docker when
  available (`tayari-runner-{lang}` images, read-only FS, no network, cap-drop,
  pids-limit 50, 256MB, 30s timeout), else subprocess with resource limits.
- `submit_code()` triggers a background AI **code review** via
  `ai/code_review.py` (imported from `ai.openai_provider`).
- **Problem statement is a hardcoded dummy**: `ProblemPanel.tsx` renders
  default props ("Write a function…", example `5\n3 → 8`). No problem data is
  fetched from the backend; the live coding room has no problem panel at all.

### 3.5 Evaluation pipeline

**Trigger paths**:
1. Manual: `POST /evaluations/{interview_id}` (works).
2. Automatic: `schedule_evaluation(session_id, user_id)` from
   `sessions/routes.py` on session end (REST `end` + WS `user.answer` wrap-up +
   WS `session.end`).

**Verified bug — automatic evaluation is broken**: the scheduler function
(`workers/scheduler.py:63`) is `schedule_evaluation(interview_id, user_id)`
and the worker (`workers/evaluation.py:39`) calls
`evaluation_service.evaluate_interview(UUID(interview_id), ...)`. But every
call site passes the **session UUID** where the interview UUID is expected
(`sessions/routes.py:135,347,400`). Session IDs and interview IDs are distinct
(`service.py` returns both). The evaluation job therefore dies looking up a
non-existent interview, so **no interview ever auto-evaluates** on completion.
Evaluations only work when triggered manually. (Verified directly.)

**Pipeline** (`evaluation/pipeline.py`):
1. `TranscriptAnalyzer` formats transcript for the prompt.
2. `get_evaluators(interview_type, provider)` returns a primary evaluator
   (coding/behavioral/system-design) + cross-cutting communication evaluator.
3. Each evaluator calls the LLM with `response_format={type:"json_object"}`
   (`gpt-4o`) and is retried up to `MAX_RETRIES=2`.
4. `ScoreAggregator.aggregate()` combines dimension scores → overall score.
5. `RecommendationService` → `ReportComposer` → `ResultValidator` →
   `EvaluationResult`.

**Scoring architecture**: all scores stored **0–5**; the frontend converts to
0–100 via `Math.round((score/5)*100)` duplicated in several components (a
normalization drift risk — see `context/ARCHITECTURE.md` ADR 5). `hire_verdict`
is categorical (`strong_hire` … `no_hire`, `error`). Results are `1:1` with an
interview (`evaluations.interview_id` unique).

**Prompt source discrepancy**: `evaluation/prompt_registry.py` loads versioned
prompts from `evaluation/prompts/{type}/v1.md`, but those directories are
**empty** — it always falls back to hardcoded default templates in
`prompt_registry.py`. The `packages/prompts/evaluators/*.md` files are used
only by the orchestrator path, not by the evaluation pipeline. Two divergent
evaluator prompt sources exist; only the hardcoded defaults are live.

**Analytics generation**: `GET /analytics` computes aggregates (total
interviews, avg score, activity, skills radar) on demand; no materialized
cache.

---

## 4. Backend Architecture

### 4.1 Feature modules

Each `features/<name>/` package contains routes, services, repositories,
schemas, models, dependencies, and tests:

| Module | Responsibility | Key files |
|---|---|---|
| `auth` | register/login/refresh/logout, email verify, password reset, social, JWT, guards, blacklist | `routes.py`, `services.py`, `guard.py`, `jwt/service.py`, `jwt/redis_blacklist.py` |
| `users` | `/users/me`, admin user management, ban/role/credits | `routes.py`, `service.py`, `repository.py` |
| `interview` | options, setup, resume/JD metadata, parse/analyze (stubs), templates, difficulty estimate | `routes.py`, `service.py` |
| `sessions` | session lifecycle REST + WS handler, event persistence, transcript persistence | `routes.py`, `service.py`, `repository.py` |
| `code` | run/submit/result/languages, rate limiting | `routes.py`, `service.py` |
| `reports` | evaluation trigger/list/get (evaluation dashboards) | `routes.py`, `service.py` |
| `dashboard` | aggregated stats + recent activity | `router.py`, `service.py` |
| `analytics` | usage analytics | `router.py` |
| `voice` | Deepgram STT proxy WS | `routes.py`, `deepgram_service.py` |
| `billing` | **Stripe stubs — all 4 endpoints return "Not implemented"** | `routes.py` |
| `email` | Resend transactional email (verify, reset) | `service.py` |
| `health` | `/health`, `/ready` (DB check) | `routes.py` |

### 4.2 Route organization & DI

- All routers mounted in `main.py` under `/api/v1` (except health at root).
- **Duplicate router registration** (verified): `main.py:265-266` imports the
  same `features.reports.routes` router under two names
  (`evaluations_router`, `reports_router`) and includes both (`277,282`),
  registering `/api/v1/evaluations/*` twice. Harmless at runtime but confusing
  and doubles route registration.
- Dependency injection via FastAPI `Depends` + factory dependencies
  (`features/*/dependencies.py`) constructing singletons (session manager,
  storage service) with per-request DB sessions.

### 4.3 Database access patterns

- SQLAlchemy 2.0 async, asyncpg; `async_session` per-request via
  `get_db()` dependency (`core/database.py`, pool 10/20, recycle 300s).
- Repository pattern: repositories take the session, never call other
  repositories; services orchestrate multiple repositories.
- `Base.metadata.create_all` runs **on every startup** (`main.py:45-46`) —
  this is the effective DDL source of truth. Alembic migrations exist (0001–0010)
  but **do not create `evaluations`, `subscriptions`, or `billing_events`**
  (0007/0009 mutate those tables), so `alembic upgrade head` on an empty DB
  fails. Also `alembic/env.py` imports only 7 of 13 model classes, so
  `--autogenerate` would propose dropping `session_events`/`submissions`/`code_reviews`.

### 4.4 Background jobs

- APScheduler (`workers/scheduler.py`) with PostgreSQL `SQLAlchemyJobStore`,
  `AsyncIOExecutor`; runs in-process with uvicorn. Jobs survive restarts
  (job store in DB) but in-flight work is not retried; `max_instances=3`.
- Evaluation worker: `workers/evaluation.py` → `EvaluationPipeline`.
- **No Celery** (ARCHITECTURE.md/README references to Celery are stale;
  verified absent from `pyproject.toml`).

### 4.5 Error handling strategy

- `core/errors.py`: `AppError` hierarchy with `status_code` + structured
  detail dict, `success_response()`, `ErrorCode` enum.
- `main.py` exception handlers: `AppError`, `RequestValidationError` (422),
  `HTTPException`, `IntegrityError` (409), `SQLAlchemyError` (500),
  catch-all `Exception` → logs + sends to Sentry, returns opaque 500.
- Every response/error includes `request_id` (ContextVar). Logging is
  structured with correlation/session IDs (`core/logging.py`).

---

## 5. Frontend Architecture

### 5.1 Structure

- **Next.js 15 App Router**, React 19, Tailwind v4, TanStack Query v5, RHF + Zod.
- Layout chain: root `app/layout.tsx` → `app/providers.tsx` (QueryClient,
  ErrorBoundary, Sentry) → `app/auth/layout.tsx` / `app/dashboard/layout.tsx`
  (Sidebar + TopNav + client-side auth gate).
- Feature-first: `features/<name>/{components,hooks,api,lib,types}`; shared UI
  in `components/` (`ui`, `shared`, `layout`, `marketing`).
- `env.ts` (t3-oss validation) is **dead code — never imported**; modules read
  `process.env.NEXT_PUBLIC_API_URL` directly with
  `http://localhost:8000/api/v1` fallback.

### 5.2 State management & API

- TanStack Query (global `staleTime: 30s`, retry 1).
- `lib/api/client.ts`: bearer-token fetch wrapper with single-flight 401-refresh
  queue; on refresh failure calls auth-failure handler (logout).
- Auth state via React context (`use-auth.tsx`).

### 5.3 Important pages

| Route | Component | Status |
|---|---|---|
| `/` | marketing sections (11) | live, dark-first theme |
| `/auth/*` | login, register, callback (Supabase OAuth), forgot/reset/verify | live |
| `/dashboard` | DashboardHome: stats, quick actions, recent, subscription, progress | live; QuickActions "Practice"/"Set Goal" buttons **no onClick** |
| `/dashboard/analytics` | custom SVG radar + bar charts | live |
| `/dashboard/reports` | evaluations list + SVG score chart | live |
| `/dashboard/settings` | profile/password/theme/danger zone | live; **Delete Account button has no onClick** |
| `/dashboard/admin/**` | user management (list/detail, role/credits/ban) | live; **protected client-side only** |
| `/dashboard/interview/new` | 4-step wizard | live |
| `/dashboard/interview/[id]` | live room (behavioral/coding/system-design) | live |
| `/dashboard/interview/[id]/coding` | standalone coding | live; dummy problem |
| `/dashboard/interview/[id]/evaluation` | evaluation dashboard (polling) | live |
| `/dashboard/billing` | **missing — sidebar links to it (behind `FF_BILLING`); enabling the flag → 404** | gap |

### 5.4 Feature flags

`lib/feature-flags.ts` defaults: `interviews:false, reports:false,
billing:false, settings:false, newInterview:true, analytics:true`.
Flags only gate **nav links**, not routes — direct URL access bypasses them.
`reports` nav item has no flag prop (always shown); `interviews`/`newInterview`
flags are never read.

### 5.5 Notable frontend gaps

- Whiteboard (`features/interview/components/whiteboard/Whiteboard.tsx`) is
  mouse-only (no touch/pointer/keyboard), fixed 800×600 canvas.
- Monaco statically imported on coding routes.
- Admin API calls fire before the `isAdmin` client-side guard, relying on
  backend 403.
- Theme: `html` hardcodes `class="dark"`; light mode applied post-mount
  (light-mode FOUC).
- Marketing `Testimonials` uses fabricated names/companies; pricing CTAs are
  "Coming Soon".

---

## 6. AI System Architecture

### 6.1 Provider integration

- `ai/provider.py` defines the `AIProvider` protocol (`chat`,
  `chat_stream`, `structured_output`); `OpenAIProvider` (async, configurable
  `base_url` for OpenRouter) and `MockProvider` (dev/tests) implement it.
- Retry: `ai/realtime/retry_policy.py` (exponential backoff + jitter +
  circuit-breaker semantics). Provider failure → orchestrator returns `None`
  (question generation fails gracefully) or session transitions to FAILED.

### 6.2 How the AI behaves like a real interviewer

- **Role prompt**: `packages/prompts/interviewers/{type}.md` — one base prompt
  per interview modality, e.g. behavioral (`behavioral.md`) and coding
  (`coding.md`) instructing the model to act as a technical interviewer rather
  than a chatbot.
- **Context injection**: `PromptBuilder.build_system_prompt()` composes:
  base interviewer prompt → company-specific instructions (from
  `packages/prompts/templates/company-specific/{company}.md`) → resume context →
  JD context → custom instructions. The model thus has the candidate's
  background and target role at conversation start.
- **Adaptive memory**: `ConversationMemory` maintains the live conversation
  window; every new question is generated with the full (bounded) history, so
  follow-ups reference prior answers. Context is dropped past 20 turns (a
  deliberate token-cost tradeoff — the interviewer can "forget" early answers
  in long interviews).
- **Turn pacing**: orchestrator caps question count by duration/type, and the
  interviewer asks one question at a time rather than emitting a block of text.
- **Hint generation**: `generate_hint()` asks the same provider with a
  coaching persona and injects it into the transcript.

### 6.3 Evaluation model

- `gpt-4o` with `response_format={"type":"json_object"}` (structured output).
- Evaluator prompts define per-dimension weights (e.g. coding: correctness 30%,
  efficiency 20%, code_quality 20%, technical_communication 15%,
  language_proficiency 15%) and demand a strict JSON schema in the system
  prompt; `ResultValidator` sanity-checks the parsed output (but swallows
  `ValidationError` in `pipeline.py:175-177`).
- **Two prompt systems coexist**: the live evaluation pipeline uses hardcoded
  defaults in `evaluation/prompt_registry.py` (its `prompts/{type}/v1.md` dirs
  are empty); the `packages/prompts/evaluators/*.md` files feed only the
  orchestrator's `evaluate()` path, which is not the one invoked by the
  worker. This is a real prompt-drift hazard.

### 6.4 Future extensibility

- Adding an evaluator = new class in `evaluation/evaluators/` + registration;
  pipeline needs no change.
- Providers are swappable via the `AIProvider` protocol.
- Prompts are versioned (`prompt_registry` supports `{type}/v{version}.md`)
  and templated — but the versioned files are not populated.

---

## 7. Realtime System Architecture

### 7.1 Session state machine

`ai/realtime/state_machine.py`: `IDLE → PREPARING → ACTIVE ⇄ PAUSED →
COMPLETING → COMPLETED`, plus `FAILED`/`TIMEOUT`. Transitions are validated by
`STATE_TRANSITIONS` + `TransitionGuard`. Helpers: `is_terminal()`,
`is_active()`, `needs_recovery()`. **In-memory only** — persisted via
snapshots to `session_events` and interview status.

### 7.2 Connection management

- `SessionManager` (`ai/realtime/session_manager.py`): dict of live sessions;
  created via `SessionService.start_session()`. Heartbeat task per WS
  (`_heartbeat_sender` in `sessions/routes.py`) pushes `timer.tick` every 5s
  and `timer.warning` under 5 min.
- `EventDispatcher` subscribes `SessionService._on_event` → persists each
  state transition to `session_events` with a monotonically increasing
  sequence number.

### 7.3 Recovery mechanisms

- Client reconnect: backoff + jitter, 10 attempts, heartbeat; `session.join`
  with `reconnect:true` → server replays `session.connected` + current
  question from the snapshot.
- Server restart: sessions restored from DB rows
  (`main.py:50-63`, `SessionRepository.find_active_sessions()`), but **without
  orchestrator/memory** — restored sessions cannot process answers (see 3.3).
- There is no ordering guarantee beyond the sequence numbers on persisted
  events; replay is "current state" not an event log replay.

### 7.4 Failure handling

| Failure | Behavior |
|---|---|
| User disconnects | WS close → `record_disconnect`; session stays ACTIVE in memory; client can reconnect within grace period |
| Server restarts | sessions restored (partial), heartbeats/AI gone; reconnection sees a session that can't answer |
| AI provider fails | orchestrator returns `None`; wrap-up/error path; retry policy absorbs transient failures |
| Network latency | token streaming + heartbeat keep UI alive; long AI latency surfaces as "thinking" with no timeout visible |
| Voice (Deepgram) drops | send_audio marks `dropped`; client receives error + must restart mic (fixed `41503a2`) |

---

## 8. Data Architecture

### 8.1 Entities (13 ORM tables)

| Table | Purpose | Key relationships |
|---|---|---|
| `users` | auth/identity, roles, soft delete | 1:N interviews, 1:N session_events, 1:1 subscription |
| `interview_templates` | seeded template definitions | — |
| `resumes` | resume metadata + parsed_content, storage_path, download_url | N:1 user |
| `job_descriptions` | JD metadata/text + parsed_content, storage_path, download_url | N:1 user |
| `interview_configurations` | denormalized wizard snapshot | N:1 user, 1:N interviews |
| `interviews` | interview row; transcript/ai_messages/device_checks JSONB; status; spoken_language; system_design_problem | N:1 user, 1:1 evaluation, FK resume/JD |
| `user_templates` | saved personal templates | N:1 user |
| `session_events` | persisted WS state transitions w/ sequence | N:1 user; no FK to interview (intentional) |
| `submissions` | code submissions | N:1 user/interview |
| `code_reviews` | AI review of a submission | N:1 submission |
| `evaluations` | 1:1 scorecard (question_scores JSONB, raw_evaluation, verdict, model_used) | 1:1 interview |
| `subscriptions` | billing (unused) | 1:1 user |
| `billing_events` | billing audit (unused) | N:1 user |

### 8.2 Storage strategy

- **PostgreSQL**: all relational + JSONB blobs (`transcript`, `ai_messages`,
  `question_scores`). No GIN indexes on JSONB; transcripts are not normalized
  to child tables.
- **Redis**: JWT blacklist (TTL keys `tayari:blacklist:{jti}`), APScheduler job
  store. **No application caching.**
- **S3/MinIO** (`core/storage.py`): abstraction over S3-compatible object
  storage with local-filesystem fallback (`./uploads/`). Currently no code
  writes file bytes — resume/JD upload is metadata-only. `generate_upload_url`
  (presigned PUT) exists but has no callers.
- **Soft delete**: `users.deleted_at`, `interviews.deleted_at` — filters are
  the responsibility of each repository (not enforced by a model-level
  `@where`).

### 8.3 Data ownership

- Users own interviews/resumes/JDs/submissions/evaluations. Ownership checks
  are performed in service layer methods (e.g. `get_interview_by_id(id, user_id)`,
  `get_resume_by_id(resume_id, user_id)`). The REST layer is generally
  ownership-checked; the **WebSocket and voice layers are not** (see 9).

---

## 9. Security Architecture

### 9.1 What exists

- **Auth**: typed JWTs (RS256 prod / HS256 dev), blacklist, refresh rotation +
  family burn, DB user re-check on every request.
- **RBAC**: `RoleChecker` / `PermissionChecker` guards; admin role from
  `ADMIN_EMAILS`.
- **Middleware**: security headers, request-id, auth audit logging
  (`core/audit.py`, email-hash in logs).
- **Input handling**: Pydantic validation everywhere; WS text sanitization
  (`_sanitize_text` strips control chars, caps length); WS message rate limit
  (10/s, sliding window per connection).
- **Code sandbox**: Docker isolation (no network, read-only, cap-drop, pid
  limit, mem limit, timeout) or subprocess with resource limits; no
  `shell=True`.
- **Prod config guard**: `core/secrets.py` aborts in prod if `JWT_SECRET_KEY`
  is default/weak.
- **Sentry** captures unhandled exceptions; audit + structured logs to stdout.

### 9.2 Verified gaps

| # | Severity | Gap | Location |
|---|---|---|---|
| 1 | **HIGH** | `POST /code/run` executes arbitrary code with **no auth** — only per-IP in-memory rate limit | `features/code/routes.py:43-57` |
| 2 | **HIGH** | Interview WS accepts any connection; no token, no ownership check | `features/sessions/routes.py:165-198` |
| 3 | **HIGH** | Voice WS unauthenticated — anyone burns Deepgram credits | `features/voice/routes.py:18-19` |
| 4 | **HIGH** | Path traversal / arbitrary file read: `storage_path` built from client-controlled `file_hash` (only length-validated) → `UPLOAD_DIR / key` | `features/interview/service.py:213,267`, `core/storage.py:165-184` |
| 5 | **MED-HIGH** | CRLF header injection via client-controlled `original_filename` in `Content-Disposition` | `features/interview/routes.py` |
| 6 | **MED** | Refresh token in `localStorage` (XSS-stealable) | `use-auth.tsx` |
| 7 | **MED** | Rate limiting is in-memory per-process, never expires entries; behind a proxy all users share the proxy IP | `core/rate_limit.py`, `code/routes.py` |
| 8 | **MED** | No login brute-force protection / account lockout | auth routes |
| 9 | **MED** | Alembic is not the source of truth; `create_all` masks missing migrations | `main.py:45-46` |
| 10 | **MED** | Admin endpoints rely on client-side gate + backend 403, but admin API calls fire for non-admins | admin pages |
| 11 | **LOW** | WS not-found branch double `accept()` throws | `sessions/routes.py:179,183` |
| 12 | **LOW** | `.env.development`/`.env.production` tracked in git (secret values empty, but credentials layout public); no secret store | root |

---

## 10. Infrastructure & Deployment

### 10.1 Docker

- Dev: `infrastructure/docker-compose.yml` — postgres:17, redis:7, minio,
  `api` (Dockerfile.dev, hot-reload), `web` (**broken: `COPY pnpm-lock.yaml`
  fails — lockfile is at repo root, and `packages/` isn't in the build/runtime
  context**). The minio healthcheck uses `mc`, which the image lacks.
- Prod Dockerfiles: `apps/api/Dockerfile` (single-stage, `uv sync --no-dev`,
  HEALTHCHECK) — sound. `apps/web/Dockerfile` multi-stage — **no
  `NEXT_PUBLIC_*` build args**, so a prod build defaults to
  `http://localhost:8000`; copies `node_modules` but not `packages/` into the
  runner (works only if Next fully bundles the workspace packages).
- Traefik config (`infrastructure/traefik/`) is **not functional**: references
  an undefined `auth` middleware, has no routers for api/web, and no shared
  network with the app containers; also uses the wrong domain (`tayari.dev`).
- `netlify.toml`: `publish = "apps/web/.next"` resolves wrong under
  `base = "apps/web"` (effective `apps/web/apps/web/.next`); SPA-fallback
  redirect to `/index.html` targets a file Next.js doesn't emit.

### 10.2 CI/CD

- `ci.yml`: lint-and-typecheck (pnpm lint/typecheck; **ruff/mypy are not
  actually run** despite the job name), js-tests (vitest), python-tests
  (pytest on Postgres+Redis services, excluding E2E), build (next build +
  perf budget), and `deploy` (**placeholder — echo only**).
- `docker.yml`: builds `tayari-api:latest` / `tayari-web:latest`, **never
  pushed to any registry**.
- **No CD, no image registry, no staging, no rollback.** README claims of
  "Railway auto-deploys" are false.

### 10.3 Hosting & environment

- No real production host configured. Env via committed templates
  (`.env.development`, `.env.production` with empty secrets) + gitignored
  `.env.local` / `apps/api/.env`.
- Frontend `NEXT_PUBLIC_*` are baked at build time; no build-time arg wiring
  in the web Dockerfile.

### 10.4 Monitoring & error tracking

- Sentry: API initialized in lifespan (traces 0.1 prod); frontend via
  `@sentry/browser` (no `@sentry/nextjs`, no SSR capture, no sourcemaps).
- Structured logs to stdout (correlation_id, session_id); audit logger JSON.
- **No `/metrics`, no Prometheus/grafana, no log aggregation, no alerting.**
  In-memory telemetry (`judge/metrics.py`, `ai/realtime/telemetry.py`) is never
  exported.
- Health: `GET /health` (static), `GET /ready` (DB check only), Docker
  HEALTHCHECK on API.

---

## 11. Current Limitations & Technical Debt

> Only issues verified from the codebase are listed. Priority reflects shipping
> risk, not cosmetic preference.

### Critical (production blockers)

1. **Background evaluation never runs** — `schedule_evaluation(session_id, …)`
   passes session IDs to a function expecting interview IDs
   (`sessions/routes.py:135,347,400` vs `workers/scheduler.py:63`,
   `workers/evaluation.py:39`). No interview auto-evaluates.
2. **Billing entirely stubbed** — 4 endpoints return "Not implemented"
   (`features/billing/routes.py`); no `/dashboard/billing` route; free-tier is
   a hardcoded count of 10 with no subscription model behind it.
3. **No deployment path** — CI deploy job is a placeholder; images never
   pushed; no CD. README/ARCHITECTURE claim otherwise.

### High priority (security & reliability)

4. **Unauthenticated code execution** (`/code/run`) — arbitrary code in a
   Docker/subprocess sandbox without auth.
5. **Unauthenticated WebSockets** — interview session WS and voice WS have no
   token/ownership verification.
6. **Path traversal** via client-controlled `file_hash` in storage paths.
7. **Alembic can't build an empty DB** — `evaluations`/`subscriptions`/
   `billing_events` have no create migrations; `create_all` masks drift.
8. **Restored sessions can't answer** — orchestrator/memory not restored;
   `process_answer` raises.
9. **Rate limiting is in-memory + no login lockout** — broken multi-instance,
   no brute-force protection.

### Medium priority (maintainability)

10. **Duplicate router registration** (`main.py:265-266,277,282`).
11. **Prompt drift** — evaluation pipeline uses hardcoded defaults; versioned
    prompt dirs empty; `packages/prompts/evaluators/*` unused by the pipeline.
12. **Dead code / config drift**: unused `env.ts`, dead feature flags
    (`interviews`, `newInterview`), `DeviceCheckStep` unwired, legacy
    `core/security.py` vs `features/auth/guard.py` dual JWT stacks, dead
    `@tayari/types` / `@tayari/ui` dependencies, dead `download_url` column
    (0010 added, never referenced).
13. **Score-scale conversion duplicated** across ≥6 components — drift risk
    (prior 1700% bug).
14. **Frontend dead CTAs**: QuickActions, SubscriptionStatus, Delete Account,
    TopNav bell/dropdown, template buttons.
15. **Stale docs**: `docs/PROJECT_STATUS.md`, README, `context/ARCHITECTURE.md`
    disagree with reality (migration count, Celery, Sentry, session restore,
    deployment, test counts).
16. **Docker compose web service broken**; Traefik config non-functional;
    `netlify.toml` wrong publish path.
17. **Resume/JD uploads are metadata-only** — no file bytes stored despite UI
    claiming upload; parse/analyze are keyword stubs.

### Low priority (optimization)

18. Monaco statically imported (~5MB) on coding routes.
19. Whiteboard mouse-only, fixed-size canvas.
20. JSONB columns without GIN indexes; dashboard aggregates computed on every
    request (no Redis caching).
21. Fabricated marketing testimonials + hardcoded demo metrics.
22. No `/metrics`/observability export; in-memory telemetry only.
23. Single uvicorn worker shares event loop for WS + REST + APScheduler.

---

## 12. Engineering Recommendations

From a Principal Engineer perspective — incremental, not rewrite.

### Correctness first (unblocks the product loop)

1. **Fix the evaluation trigger** (~3 lines): pass `session.interview_id`
   instead of `session_id` at `sessions/routes.py:135,347,400` (or change
   `schedule_evaluation` to resolve interview from session). Then add an
   integration test that end-session → job → evaluation row. This is the
   single highest-value fix.
2. **Decide billing**: either remove the stub routes + nav link + flag (cheapest
   honest option for launch), or implement Stripe checkout/portal/webhook with
   signature verification. Do not ship a page that 404s.

### Close the security surface

3. Add `get_current_user` to `/code/run` and bind a user identity to
   submissions; move to Redis-backed rate limiting keyed by user.
4. Authenticate both WebSockets: validate the access token on connect (query
   param/token payload is fine for browsers) and check session ownership
   (`session.user_id == current_user.id`).
5. Sanitize `file_hash` (allow `[a-f0-9]{64}`) and CRLF-strip `original_filename`
   before building storage paths / headers.
6. Add Alembic create-migrations for `evaluations`/`subscriptions`/`billing_events`,
   register the 3 missing models in `alembic/env.py`, and run
   `alembic upgrade head` (not `create_all`) in CI and deploy. Add a migration
   drift check (`alembic check`) to CI.

### Reliability

7. Restore orchestrator/memory for restarted sessions, or refuse reconnection
   explicitly (fail fast rather than silently accepting answers that crash).
8. Move evaluation/scheduler to a dedicated worker process so the event loop
   isn't shared with WS/REST and so evaluations survive app restarts.
9. Add DB-level guard or `SELECT … FOR UPDATE` around the free-tier cap.

### Deployment & observability

10. Wire `NEXT_PUBLIC_*` build args into `apps/web/Dockerfile`; fix the compose
    web build (copy lockfile from root + mount `packages/`); fix/remove
    `netlify.toml` redirects; delete the broken Traefik config or fix it.
11. Make CI run ruff + mypy (the job claims to), push images to GHCR/ECR, and
    replace the placeholder `deploy` with a real target (Fly/Render/Railway or
    a managed VPS + systemd).
12. Export metrics (`/metrics` Prometheus or vendor SDK), ship logs to a sink,
    and set alerting on 5xx + AI-provider error rate. Add Sentry to SSR via
    `@sentry/nextjs`.

### Maintainability & DX

13. Deduplicate the score-scale conversion into a shared util (e.g.
    `lib/score.ts` in web, `score_from_5()`), and update all components.
14. Delete dead code: `env.ts`, unused flags, `DeviceCheckStep`, legacy
    `core/security.py` get_current_user, `@tayari/types`/`@tayari/ui` if unused,
    the `download_url` column or wire it. Remove the duplicate router import.
15. Single source of truth for evaluator prompts: populate
    `evaluation/prompts/{type}/v1.md` from `packages/prompts/evaluators/*.md`
    and add a test that the pipeline's loaded prompt matches the package
    template.
16. Bring docs into alignment: correct migration count (10), remove Celery
    claims, correct deployment claims, update `docs/PROJECT_STATUS.md` and
    test counts.
17. Add CI gating: coverage thresholds, Playwright E2E in CI (with
    `webServer`), and dependency/security scanning (gitleaks/trivy/audit).

---

## Appendix — Document/Implementation Discrepancies

| Claim (docs) | Reality (code) |
|---|---|
| "CI runs ruff + mypy" | `ci.yml` lint job runs pnpm lint/typecheck only; no ruff/mypy step |
| "Railway auto-deploys API, Netlify auto-deploys frontend" | No deploy workflow; CI `deploy` is an echo; `netlify.toml` broken |
| "Celery dependency" | Celery absent from `pyproject.toml` |
| "Sentry not initialized" (older) | Sentry initialized in `main.py` lifespan (API) + `@sentry/browser` (web) |
| "8 migrations" | 10 migrations, head `0010`; PG 17 (not 18) |
| "Sessions are not restored on restart" | `main.py` restores sessions, but orchestrator/memory are not restored |
| "MemoryBlacklist" | Redis blacklist used when `REDIS_URL` non-localhost; Memory fallback in dev |
| `JWT_SECRET_KEY` default "change-me" | present; prod guard aborts on weak key |
| `context/code-standards.md` required by AGENTS.md | **file does not exist** |
| "File stored in S3-compatible bucket" | no file bytes written; metadata only |
