# Tayari AI

> AI-powered mock interview platform for software engineers. Live voice conversations with a trained AI interviewer across coding, system design, and behavioral formats — with scored evaluations and progress tracking.

[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=fff)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=fff)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000?logo=nextdotjs&logoColor=fff)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=fff)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=fff)](https://www.postgresql.org/)
[![pnpm](https://img.shields.io/badge/pnpm-9-F69220?logo=pnpm&logoColor=fff)](https://pnpm.io/)
[![Turborepo](https://img.shields.io/badge/Turborepo-2-EF4444?logo=turborepo&logoColor=fff)](https://turbo.build/repo)

---

## Architecture

```
                    Cloudflare CDN
                           │
                  ┌────────┴────────┐
                  │                 │
            Vercel Hobby      Railway / Fly.io
           (Next.js 15 app)   (FastAPI backend)
                  │                 │
                  └────────┬────────┘
                           │
                    FastAPI (modular monolith)
                           │
              ┌────────────┼────────────┐
              │            │            │
         Neon PG 17    Cloudflare R2   APScheduler
         (primary DB)  (objects)       (bg tasks)

         WebSocket (interview events)
         WebRTC   (audio, post-MVP)
```

The backend is a **feature-based modular monolith** — each domain (auth, interview, reports, billing, users, voice) owns its models, schemas, routes, and services. This keeps boundaries clean without paying the operational cost of microservices.

---

## Tech Stack

| Layer | Technology | Cost |
|---|---|---|
| Frontend | Next.js 15 + React 19 + TypeScript | Free (Vercel Hobby) |
| UI | Tailwind CSS v4 + shadcn/ui | Free |
| State | TanStack Query | Free |
| Backend | FastAPI + Python 3.13 + uvicorn | Free (Railway/Fly.io) |
| Package mgmt | uv (Python) + pnpm (Node) | Free |
| Database | PostgreSQL 17 (Neon free tier) | Free (500MB) |
| ORM | SQLAlchemy 2 (async) + Alembic | Free |
| Cache | Redis 7 (upstash/self-hosted post-MVP) | Free tier |
| Auth | Custom JWT (RS256) | Free |
| Voice (MVP) | Web Speech API + Speech Synthesis API | Free (browser APIs) |
| Voice (future) | OpenAI Realtime API | Paid |
| AI Interviewer | GPT-4o-mini | ~$0.06-0.18/interview |
| AI Evaluator | GPT-4o | ~$0.03-0.05/interview |
| Code Execution | Pyodide + QuickJS (client-side WASM) | Free |
| Storage | Cloudflare R2 | Free (10GB) |
| Email | Resend | Free (500/mo) |
| Payments | Stripe | Per-transaction fee |
| Background Jobs | APScheduler (MVP) → Celery + Redis (later) | Free |
| Monitoring | Sentry + Prometheus + Grafana | Free tiers |
| CI/CD | GitHub Actions | Free (2000 min/mo) |

---

## Project Structure

```
ai-interview-platform/
├── apps/
│   ├── web/                    # Next.js 15 (App Router, RSC)
│   │   ├── app/
│   │   ├── features/           # Feature-sliced UI modules
│   │   ├── lib/api/            # Typed API client
│   │   └── env.ts              # t3-env validated env vars
│   └── api/                    # FastAPI modular monolith
│       ├── core/               # Config, DB, security, errors, logging, rate limiting
│       ├── features/           # Domain modules
│       │   ├── auth/           # Auth models, schemas, routes, services
│       │   ├── interview/      # Interview lifecycle
│       │   ├── reports/        # Evaluation generation
│       │   ├── billing/        # Stripe integration
│       │   ├── users/          # Profile management
│       │   └── voice/          # WebSocket audio streaming
│       ├── ai/                 # AI provider abstraction (ABC → OpenAI)
│       └── workers/            # Background job definitions
├── packages/
│   ├── ui/                     # Shared React components (shadcn)
│   ├── types/                  # Zod schemas shared between web + api
│   ├── config/                 # ESLint, TypeScript configs
│   └── prompts/                # Version-controlled AI system prompts
├── architecture/               # ADRs, C4 diagrams, ERD
│   ├── decisions/              # Architecture Decision Records
│   ├── C4/                     # Context + Container diagrams
│   └── database/               # DBML entity relationship diagram
├── infrastructure/             # Docker, Traefik, Terraform (future)
└── docs/                       # PRD, SRS, AI architecture docs
```

---

## Features

### MVP (Phase 1 — shipped)

| Feature | Status |
|---|---|
| Email/password authentication | Scaﬀolded |
| Interview setup wizard (type → company → level) | Scaﬀolded |
| Coding interview room (Monaco + WASM execution) | Scaﬀolded |
| Pseudo-realtime voice (Browser Speech API) | Scaﬀolded |
| AI interviewer (GPT-4o-mini) | Scaﬀolded |
| Post-interview evaluation (GPT-4o) | Scaﬀolded |
| Interview history with scores | Scaﬀolded |
| Stripe checkout + subscription management | Scaﬀolded |
| Company directory (665+) | Planned |
| Concept directory (71 algorithms) | Planned |

### Post-MVP (Phase 2+)

- System design interviews (Excalidraw canvas)
- Behavioral interviews (STAR framework)
- OpenAI Realtime API (true low-latency voice)
- Resume / job description parsing
- Admin dashboard
- Admin portal (users, revenue, feature flags)

---

## Getting Started

### Prerequisites

- Python 3.13 (`uv` for dependency management)
- Node.js 22 (`pnpm` for package management)
- Docker Desktop (for local PostgreSQL + Redis)

### Clone and install

```bash
git clone https://github.com/Mahnoor-Zaffar/Tayari.ai.git
cd Tayari.ai

# Install Python dependencies
cd apps/api
uv sync --dev
cd ../..

# Install Node dependencies
pnpm install
```

### Environment setup

```bash
cp .env.example .env.local
# Edit .env.local with your API keys:
#   OPENAI_API_KEY, STRIPE_SECRET_KEY, RESEND_API_KEY
```

### Start local development

```bash
# Start PostgreSQL + Redis
docker compose -f infrastructure/docker-compose.yml up -d

# Start API (FastAPI with hot reload)
cd apps/api && uv run uvicorn main:app --reload

# Start Web (Next.js with hot reload)
cd apps/web && pnpm dev
```

### Run database migrations

```bash
cd apps/api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Verify

- Web: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Modular monolith over microservices | Faster to ship, cheaper to operate, easier to extract later |
| Client-side WASM (Pyodide + QuickJS) for code execution | Zero server cost, no network latency for compile/run |
| Browser Speech API over OpenAI Realtime for MVP | $0 vs ~$1.80/interview in audio costs |
| Custom JWT over Better Auth | Works natively with FastAPI, no vendor lock-in |
| Manual Zod + Pydantic over OpenAPI codegen | Simple, full type control, no build step |
| APScheduler over Celery for MVP | No Redis dependency until queue volume justiﬁes it |

See `architecture/decisions/` for full Architecture Decision Records.

---

## Performance Budgets

| Metric | Target |
|---|---|
| Voice chunk roundtrip (STT → AI → TTS) | <2s P95 |
| Code execution (Python WASM) | <500ms P95 |
| Page load (interview setup) | <2s LCP |
| API response (non-AI) | <200ms P95 |
| Evaluation generation (ﬁrst token) | <3s |
| WebSocket reconnection | <2s |

---

## Monitoring & Observability

- **Errors:** Sentry (error tracking with request/session/interview context)
- **Metrics:** Prometheus + Grafana (API latency, AI latency, token usage, DB pool)
- **Analytics:** PostHog (user behavior, conversion funnels, feature usage)
- **Health:** UptimeRobot (synthetic checks on /health)

---

## AI Cost Strategy

Tayari is designed to operate on a tight AI budget. Every interview is capped:

| Component | Model | Est. Cost/Session |
|---|---|---|
| Interviewer (30 min) | GPT-4o-mini | $0.06-0.18 |
| Evaluator (post-session) | GPT-4o | $0.03-0.05 |
| **Total** | | **$0.09-0.23** |

Hard cap: **$0.30/interview**. If exceeded, the interviewer degrades to GPT-4o-mini with reduced context.

---

## Architecture Documentation

- `01_Reverse_Engineering_Report.md` — Full site analysis, data model, API spec, edge cases
- `02_PRD.md` — Product requirements, MVP scope, free-tier constraints
- `architecture/decisions/` — ADR-001 (monorepo), ADR-002 (voice), ADR-003 (AI provider)
- `architecture/C4/` — C4 context + container diagrams (Mermaid)
- `architecture/database/erd.dbml` — Entity relationship diagram

---

## License

MIT

---

*Built with pnpm, Turborepo, FastAPI, and Next.js — deployed on free tiers, designed for production.*
