# Tayari AI

AI-powered mock interview platform for software engineers. Real-time voice conversations with a trained AI interviewer across coding, system design, and behavioral formats — with scored evaluations and progress tracking.

[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=fff)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=fff)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000?logo=nextdotjs&logoColor=fff)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=fff)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=fff)](https://www.postgresql.org/)
[![pnpm](https://img.shields.io/badge/pnpm-9-F69220?logo=pnpm&logoColor=fff)](https://pnpm.io/)
[![Turborepo](https://img.shields.io/badge/Turborepo-2-EF4444?logo=turborepo&logoColor=fff)](https://turbo.build/repo)

---

## Overview

Tayari conducts live, AI-driven technical interviews. A candidate joins a WebSocket-powered session, answers questions via voice (Deepgram STT) or text, and receives a structured evaluation after completion. Three interview modalities are supported:

- **Coding** — Algorithmic problem-solving with Monaco editor
- **System Design** — Whiteboard-style architecture discussion
- **Behavioral** — STAR-method leadership and collaboration questions

The AI interviewer is prompt-driven (not fine-tuned) with per-company and per-modality templates in `packages/prompts/`. Evaluations run asynchronously via APScheduler after the interview completes.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15 (App Router), React 19, TypeScript, Tailwind v4 |
| State | TanStack Query, framer-motion |
| Backend | FastAPI, Python 3.13, uvicorn |
| Package mgmt | uv (Python), pnpm 9 (Node) — monorepo via Turborepo |
| Database | PostgreSQL 17 via asyncpg, SQLAlchemy 2.0 async, Alembic |
| Cache | Redis 7 |
| Auth | Custom JWT (RS256/HS256) with refresh token rotation |
| Realtime | WebSocket (first-party, no Socket.IO), heartbeat monitoring |
| STT | Deepgram (nova-3 model) |
| AI | OpenAI-compatible (OpenRouter) — GPT-4o-mini (interviewer), GPT-4o (evaluator) |
| Email | Resend |
| Background Jobs | APScheduler with PostgreSQL job store |
| Code Editor | Monaco |
| CI/CD | GitHub Actions (lint, typecheck, test, build) |
| Containerization | Docker Compose (Postgres, Redis, API, Web) |
| Reverse Proxy | Traefik v3 (infrastructure config provided) |

---

## Repository Structure

```
ai-interview-platform/
├── apps/
│   ├── web/                         # Next.js 15 (App Router)
│   │   ├── app/
│   │   │   ├── auth/                # Login, register, password reset, verify email
│   │   │   ├── dashboard/           # Main app (interviews, reports, admin)
│   │   │   └── ...
│   │   ├── features/                # Feature-sliced UI modules
│   │   │   ├── auth/                # AuthProvider, useAuth, forms
│   │   │   ├── interview/           # Setup wizard, session client, components
│   │   │   ├── dashboard/           # Stats grid, activity list, widgets
│   │   │   ├── evaluation/          # Score cards, radar chart, transcript viewer
│   │   │   ├── coding/              # Monaco editor, code session, test panel
│   │   │   ├── reports/             # Report dashboard
│   │   │   └── admin/               # User management
│   │   ├── lib/api/                 # Typed API client with auto-refresh
│   │   └── components/              # Shared UI (shadcn/ui style)
│   └── api/                         # FastAPI modular monolith
│       ├── core/                    # Config, database, audit logging, middleware
│       ├── features/
│       │   ├── auth/                # JWT, password hashing, guards, routes
│       │   ├── interview/           # CRUD, setup wizard, configuration
│       │   ├── sessions/            # WebSocket session persistence, reconnect
│       │   ├── reports/             # Evaluation pipeline, score persistence
│       │   ├── billing/             # Stripe stubs (not yet wired)
│       │   ├── users/               # Admin user management
│       │   ├── voice/               # Deepgram STT integration
│       │   ├── code/                # Code submission + review
│       │   ├── dashboard/           # Aggregated stats
│       │   └── analytics/           # Usage analytics
│       ├── ai/                      # AI provider abstraction + realtime engine
│       │   ├── provider.py          # ABC: chat, chat_stream, structured_output
│       │   ├── openai_provider.py   # OpenAI/OpenRouter implementation
│       │   ├── mock_provider.py     # Dev-mode canned responses
│       │   ├── code_review.py       # AI code review service
│       │   └── realtime/            # Session state machine, orchestrator,
│       │                             # memory, transcript, heartbeat, telemetry
│       └── workers/                 # APScheduler integration + evaluation worker
├── packages/
│   ├── prompts/                     # Version-controlled AI prompt templates
│   │   ├── interviewers/            # coding.md, system-design.md, behavioral.md
│   │   ├── evaluators/              # Per-modality evaluation rubrics
│   │   └── templates/company-specific/  # Google, Amazon, Meta interview styles
│   ├── types/                       # Zod schemas shared web↔api
│   ├── config/                      # Shared ESLint + TypeScript configs
│   └── ui/                          # Shared React components
├── infrastructure/                  # Docker Compose, Traefik config
├── .github/workflows/               # CI (lint, test, build, docker)
└── ARCHITECTURE.md                  # Full system architecture reference
```

---

## Key Design Decisions

- **Modular monolith** over microservices — each domain owns its models, routes, services, and tests within `features/`. Clean boundaries without operational overhead.
- **In-memory session manager** with DB snapshots — live interview state is a Python dataclass dict. Snapshots persist to PostgreSQL on transitions. This avoids per-turn DB latency (sub-ms state changes vs. 5-15ms round trips) at the cost of session loss on process restart.
- **APScheduler over Celery** — background evaluations run in-process with `SQLAlchemyJobStore`. Survives restarts. No Redis dependency for the MVP queue volume. Celery is declared as a dependency but unused.
- **Custom JWT with refresh rotation** — short-lived access tokens (24h), long-lived refresh tokens (7d) with rotation. Revoked tokens share a `token_family` — reuse detection blocks replay attacks.
- **Feature-first auth guards** — `get_current_user`, `RoleChecker`, `PermissionChecker` composable dependencies. Admin detection is email-based (`admin@tayari.ai`).
- **Prompt-driven AI** — no fine-tuning. Interviewer behavior is controlled entirely by `packages/prompts/*.md` templates. Per-company style notes (Google, Amazon, Meta) modify tone and focus areas.

For detailed trade-off analysis, see [ARCHITECTURE.md](ARCHITECTURE.md#5-design-decisions--trade-offs-adrs).

---

## Getting Started

### Prerequisites

- Python 3.13+, Node.js 22+, pnpm 9+
- Docker Desktop (for local PostgreSQL + Redis)
- uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Install

```bash
git clone https://github.com/Mahnoor-Zaffar/Tayari.ai.git
cd Tayari.ai

# Start infrastructure
docker compose -f infrastructure/docker-compose.yml up -d db redis

# Install Python deps
cd apps/api
uv sync --all-extras
uv run alembic upgrade head
uv run python scripts/seed.py
cd ../..

# Install JS deps
pnpm install

# Start development (turbo runs API + Web concurrently)
pnpm dev
```

### Verify

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Environment

Copy and edit the API env file:

```bash
cp apps/api/.env.example apps/api/.env
# Set OPENAI_API_KEY, RESEND_API_KEY, etc.
```

Frontend env vars are in `apps/web/.env.local` (pre-configured for local dev).

---

## Testing

```bash
# Backend (requires PostgreSQL + Redis running)
cd apps/api
uv run pytest tests/ --ignore=tests/test_e2e_evaluation.py -v

# Frontend
pnpm --filter @tayari/web test

# All lint + typecheck
pnpm lint
pnpm typecheck
```

Pre-commit hooks (`ruff check --fix` + `ruff format` + `pytest`) run automatically on `git commit`.

---

## CI/CD

GitHub Actions runs on push/PR to `main` or `feature/**`:

1. **Lint & TypeCheck** — ruff, mypy, eslint, tsc
2. **JS Tests** — vitest (92 tests)
3. **Python Tests** — pytest with PostgreSQL 17 + Redis 7 service containers (437+ tests)
4. **Build** — next build + performance budget check
5. **Docker** — builds production images for API (multi-stage Python) and Web (multi-stage Next.js)

---

## Current State

### What works
- Full auth flow (register, login, logout, refresh, email verification, password reset)
- Interview setup wizard (3 types, config presets, resume/JD upload)
- Coding interviews with Monaco editor + live AI interviewer via WebSocket
- System design interviews with whiteboard canvas
- Behavioral interviews with STAR-based AI interviewer
- Deepgram voice transcription (300ms → 2000ms endpointing)
- Token-streaming AI responses with auto-scroll
- Session reconnection with jittered backoff (max 10 attempts) + state replay
- Post-interview evaluation via background APScheduler worker
- Dashboard (stats grid, activity list, interview progress, subscription status)
- Evaluation reports with radar charts and dimension scores
- Admin user management
- Transactional email (password reset, email verification)
- Error/loading/empty states across all major surfaces
- Mobile-responsive interview session UI

### What's in development / stubbed
- Stripe billing — all 4 routes return "Not implemented"
- Celery integration — dependency declared, never wired
- S3-compatible storage — config exists, no code uses it
- E2E tests — excluded from CI

---

## Architecture Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — Full system reference: architecture, data model, API contracts, ADRs, operational runbooks, security model, technical debt inventory

---

## License

MIT
