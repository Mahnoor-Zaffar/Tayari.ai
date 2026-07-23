# Tayari AI — Project Status Report

**Date:** July 22, 2026
**Latest Commit:** `ef85c76` (fix: update tests to match active status and new fields)
**Branch:** `main` (up to date with origin)

---

## Overview

AI-powered mock interview platform. Candidates practice live conversational interviews with an AI interviewer across coding, system design, and behavioral formats. Includes real-time voice (Deepgram streaming), Monaco code editor, system-design whiteboard, scored evaluations, and progress tracking.

**Stack:** Next.js 15 (frontend) + FastAPI (backend) + PostgreSQL 18 + pnpm monorepo with Turborepo. Python 3.13, TypeScript 5.5.

---

## Codebase Stats

| Metric | Count |
|--------|-------|
| Python files (apps/api) | ~630 |
| TS/TSX files (apps/web) | ~163 |
| Backend tests | 425 passing, 2 failing (1 E2E needs server, 1 flaky auth test) |
| DB migrations | 8 (head: 0008) |
| Frontend pages | 11 route pages |
| Git commits | 150+ |

---

## Architecture

### Monorepo (`pnpm workspace`)
```
tayari-ai/
├── apps/
│   ├── api/          # FastAPI (Python 3.13)
│   └── web/          # Next.js 15 (React 19, TypeScript)
├── packages/
│   ├── types/        # Shared TypeScript types
│   └── prompts/      # AI prompt templates (interviewers + evaluators)
├── architecture/     # Docs, diagrams, PRD, reverse-engineering report
└── docs/             # Project status docs
```

### Backend Modules (feature-first)
```
features/
├── analytics/     — Score trends time-series
├── auth/          — JWT login, registration
├── billing/       — Stripe subscriptions (stub)
├── code/          — Coding submission endpoints
├── dashboard/     — Aggregate stats, streak, recent activity
├── health/        — Health check endpoints
├── interview/     — Setup wizard, CRUD, uploads, templates
├── reports/       — Evaluation CRUD, list, triggers
├── sessions/      — WebSocket session lifecycle, REST
├── users/         — User profile
└── voice/         — Deepgram streaming proxy WS
```

### AI Runtime (`apps/api/ai/realtime/`)
```
├── event_dispatcher.py   — Pub/sub for session events
├── heartbeat.py          — Keep-alive monitor
├── memory_manager.py     — Conversation memory (system prompt + messages)
├── orchestrator.py       — AIOrchestrator: drives Q&A flow
├── prompt_builder.py     — Loads + interpolates prompt templates
├── retry_policy.py       — Exponential backoff
├── session_manager.py    — Session state machine, lifecycle
├── state_machine.py      — FSM: idle→preparing→active→paused→completing→completed→failed
├── structured_log.py     — Structured logging helpers
├── telemetry.py          — Session metrics collection
└── transcript_manager.py — Turns + transcript storage
```

### Evaluation Pipeline (`apps/api/evaluation/`)
```
├── pipeline.py           — Main orchestrator
├── types.py              — Dataclasses (DimensionScore, QuestionScore, EvaluationResult)
├── aggregator.py         — Merges multi-evaluator results
├── composer.py           — Builds final EvaluationResult
├── validator.py          — Parses AI JSON, normalizes scores
├── sanitize.py           — PII redaction, injection prevention
├── transcript_analyzer.py— Parses raw transcript into structured turns
├── code_analysis.py      — Code submission analysis
├── recommendations.py    — Generates tips by dimension
├── evaluators/           — Per-type evaluators (coding, behavioral, system_design)
└── prompt_registry.py    — Default evaluator prompts
```

---

## Current State

### ✅ What Works

**Interview Lifecycle:**
- Full setup wizard (4 steps): Interview Type → Preferences → Uploads → Review
- Interview creation with all config options stored in DB + configuration snapshot
- Session FSM with 9 states, WebSocket signaling, event persistence
- Heartbeat monitoring, auto-reconnect, pause/resume
- Interview status transitions: pending → active → completed
- Transcript persistence to interview record on session end

**AI Interviewer:**
- OpenRouter integration (`gpt-4o-mini` for interviewer, `gpt-4o` for evaluator)
- All wizard config now flows into AI prompts: `difficulty`, `duration`, `role`, `framework`, `spoken_language`, `company`, `language`, `experience_level`, `custom_instructions`, resume/JD context, `system_design_problem`
- Company-specific prompt templates (Google, Amazon, etc.)
- Prompt builder with caching by config hash

**Voice (Deepgram Streaming):**
- Browser → AudioWorklet (16kHz PCM) → Backend WS → Deepgram WS proxy
- Auto-start mic when question arrives
- Speaking indicator, audio level bar, language badge (EN/UR)
- Auto-submit on speech_final (silence detection)
- Interrupt/cancel, reconnection with exponential backoff
- Spoken language selector (English, Urdu)

**Coding Interviews:**
- Monaco editor with 7 languages (Python, Java, C++, JS, C#, etc.)
- Language initialized from wizard selection (not hardcoded to Python)
- Run/submit code, custom test input, test results panel
- Code execution via secure Judge module (Docker sandbox)

**System Design Interviews:**
- Canvas-based whiteboard with shapes, text, drawing, export
- Wizard now has "Design Problem" text input (shown for system-design type)
- Problem statement passed to AI system prompt

**Evaluation Dashboard:**
- Score radar chart, score ring, category breakdown
- Question-by-question review (PracticeReview component)
- Per-question dimension scores and re-answer feature
- Trigger evaluation button, "No evaluation yet" state

**Dashboard:**
- Stats grid (total, completed, active, streak, avg score)
- Interview progress card with latest evaluation score
- Recent activity list
- Evaluation results now display with correct 0–5 → percentage conversion

**Reports:**
- Score history, stats, evaluation list
- Analytics time-series (daily/weekly/monthly) — backend implemented

### ⚠️ Known Issues / Bugs

1. **5 failing tests in test suite** (425 passing):
   - `test_e2e_evaluation.py` — Needs running server + fresh DB state
   - `test_auth_guard.py::test_returns_user_on_valid_token` — Flaky fixture resolution

2. **Evaluation processing is synchronous** — The `POST /evaluations/{id}` endpoint blocks until the AI responds. No polling/progress indicator while evaluating.

3. **Analytics hook unused** — `useAnalytics()` exists but no UI component renders it.

4. **No score trend comparison** on dashboard — Time-series analytics exist in backend but not surfaced.

5. **Coding/System Design layouts lack voice input** — Only the behavioral InterviewSession has the Deepgram voice pipeline.

6. **`credits_remaining` always 0** — The field exists in the dashboard schema but is never computed from subscriptions.

7. **InterviewConfiguration snapshot is write-only** — Written at creation but never read back when sessions start.

8. **Free-tier limit** hardcoded at 10 interviews (configurable in `features/interview/service.py:38`).

### ❌ Not Yet Implemented

- Stripe billing integration (stubs only)
- CI/CD pipeline (Docker Compose dev setup exists)
- Production monitoring (Sentry stubs)
- Full-text resume parsing (keyword-based only)
- User account management (change password, delete account)
- Email notifications (Resend stub)
- Admin dashboard
- Multi-session / concurrency edge cases for same user

---

## Frontend Routes

| Route | Component |
|-------|-----------|
| `/` | Landing page |
| `/auth/login` | Login form |
| `/auth/register` | Registration |
| `/auth/forgot-password` | Password reset |
| `/dashboard` | Dashboard home (stats, progress, activity) |
| `/dashboard/interview/new` | Setup wizard (4 steps) |
| `/dashboard/interview/[id]` | Interview session (coding/system-design/behavioral) |
| `/dashboard/interview/[id]/evaluation` | Evaluation results page |
| `/dashboard/interview/[id]/coding` | Legacy coding page |
| `/dashboard/reports` | Reports dashboard (score history) |

---

## Key API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/auth/login` | JWT login |
| POST | `/api/v1/interviews` | Create interview |
| GET | `/api/v1/interviews/options` | Wizard options |
| POST | `/api/v1/sessions` | Start session |
| WS | `/api/v1/sessions/{id}/ws` | WebSocket session |
| POST | `/api/v1/evaluations/{id}` | Trigger evaluation |
| GET | `/api/v1/evaluations/{id}` | Get evaluation result |
| GET | `/api/v1/dashboard` | Dashboard stats |
| GET | `/api/v1/analytics` | Score time-series |
| POST | `/api/v1/code/execute` | Run code |
| POST | `/api/v1/code/submit` | Submit code |
| WS | `/api/v1/voice/ws` | Deepgram streaming WS |

---

## DB Schema (8 migrations)

Core tables: `users`, `interviews`, `interview_configurations`, `resumes`, `job_descriptions`, `interview_templates`, `user_templates`, `session_events`, `submissions`, `code_reviews`, `evaluations`, `subscriptions`

**Interview model** columns: `id, user_id, type, company, role, experience_level, language, spoken_language, difficulty, duration_minutes, framework, custom_instructions, system_design_problem, resume_id, job_description_id, template_id, configuration_id, status, timer_remaining, transcript, ai_messages, created_at, updated_at, deleted_at, started_at, completed_at, cancelled_at`

---

## Setup & Run

```bash
# Backend
cd apps/api
cp .env.example .env  # configure DB + API keys
.venv/bin/alembic upgrade head
.venv/bin/uvicorn main:app --reload

# Frontend
cd apps/web
pnpm dev
```

**Key env vars:** `DATABASE_URL`, `JWT_SECRET`, `OPENROUTER_API_KEY`, `DEEPGRAM_API_KEY`

---

## Recent Changes (Last 2 Sessions)

1. **Dashboard progress bugs fixed** — Interview status lifecycle (pending→active→completed), dashboard status query uses `"active"` not `"in_progress"`, score display uses correct 0–5→percentage conversion, "No evaluation yet" state added.

2. **All interview config wired to AI prompts**:
   - `difficulty` no longer conflated with `experience_level`
   - `duration_minutes` replaces hardcoded "30 minutes" in prompts
   - `{role}` and `{framework}` placeholders added
   - `spoken_language` tells AI which language to use
   - Resume/JD parsed content loaded and sent to AI (was hardcoded `None`)
   - `system_design_problem` — new field + migration 0008 + wizard text input + prompt interpolation
   - `{problem}` and `{missing_aspect}` in system design prompts use actual values

3. **Coding editor** initializes from wizard language selection (not hardcoded Python).

4. **Migration 0008** added `system_design_problem` column to `interviews` and `interview_configurations`.

---

## Database status

To clear free-tier limit for testing:
```bash
psql -U tayari -d tayari -c "UPDATE interviews SET deleted_at = now() WHERE deleted_at IS NULL;"
```

Admin account: `admin@tayari.ai` / `Tayari123!`
