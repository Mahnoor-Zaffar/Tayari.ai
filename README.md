<p align="center">
  <img src="assets/screenshots/hero.svg" alt="Tayari AI" width="100%" />
</p>

<h1 align="center">Tayari AI</h1>

<p align="center">
  <strong>AI-powered mock interview platform for software engineers.</strong>
</p>

<p align="center">
  Live voice conversations with an AI interviewer across coding, system design, and behavioral formats — with structured evaluations, dimension scoring, and progress tracking.
</p>

<p align="center">
  <a href="#features"><img src="https://img.shields.io/badge/Docs-Read%20the%20docs-blue?style=flat-square" alt="Docs" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License" /></a>
  <a href="https://github.com/Mahnoor-Zaffar/Tayari.ai/actions"><img src="https://img.shields.io/github/actions/workflow/status/Mahnoor-Zaffar/Tayari.ai/ci.yml?style=flat-square&label=CI" alt="CI" /></a>
  <br />
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-15-000?style=flat-square&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/TypeScript-5.5-3178C6?style=flat-square&logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat-square&logo=postgresql" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/pnpm-9-F69220?style=flat-square&logo=pnpm" alt="pnpm" />
  <img src="https://img.shields.io/badge/Turborepo-2-EF4444?style=flat-square&logo=turborepo" alt="Turborepo" />
</p>

---

## Features

<table>
  <tr>
    <td width="50%">
      <h3>🔐 Authentication</h3>
      <p>Email/password registration and login with JWT access/refresh token rotation. Email verification and password reset flows via Resend. Role-based access control with admin and user roles.</p>
    </td>
    <td width="50%">
      <h3>🤖 AI Interview Engine</h3>
      <p>Real-time WebSocket-powered interview sessions with an AI interviewer. State-machine-managed session lifecycle: prepare → active → paused → completed. Token-by-token AI response streaming.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>💻 Coding Interviews</h3>
      <p>Monaco editor with syntax highlighting, multiple language support (Python, JavaScript, TypeScript, Java, C++, Go, Rust), and a Docker-based code execution sandbox with isolated test case evaluation.</p>
    </td>
    <td width="50%">
      <h3>📊 AI Evaluation</h3>
      <p>Post-interview evaluation via GPT-4o with structured output. Scores across multiple dimensions (problem-solving, code quality, communication), hire verdicts, strengths/improvements, and question-level breakdowns.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎙️ Real-time Voice</h3>
      <p>Deepgram STT integration (nova-3 model) with configurable endpointing. Browser-based audio capture with live transcription and auto-submit on silence detection.</p>
    </td>
    <td width="50%">
      <h3>⚡ Session Resilience</h3>
      <p>WebSocket reconnection with jittered exponential backoff (10 max attempts), session state replay on reconnect, heartbeat monitoring, and database-backed session persistence across server restarts.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📈 Dashboard & Reports</h3>
      <p>Aggregated statistics, interview progress tracking, recent activity list, subscription status, and performance trend charts. Per-interview evaluation reports with radar charts and dimension scores.</p>
    </td>
    <td width="50%">
      <h3>📄 Resume & JD Analysis</h3>
      <p>Upload and parse resumes (PDF/DOCX) and job descriptions. Keyword-based technology extraction and language suggestion. S3-compatible storage backed by MinIO for local dev and Supabase Storage for production.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>⚙️ Production Features</h3>
      <p>Sentry error tracking (backend + frontend), Redis-backed JWT blacklist, structured audit logging, APScheduler background jobs, feature flags, configurable CORS, and Docker Compose infrastructure.</p>
    </td>
    <td width="50%">
      <h3>🎭 Three Interview Modalities</h3>
      <p><strong>Coding</strong> — algorithmic problem-solving with live editor<br /><strong>System Design</strong> — whiteboard-style architecture discussion<br /><strong>Behavioral</strong> — STAR-method leadership and collaboration questions</p>
    </td>
  </tr>
</table>

---

## Screenshots

<p align="center">
  <img src="assets/screenshots/hero.svg" alt="Landing Page" width="49%" />
  <img src="assets/screenshots/dashboard.svg" alt="Dashboard" width="49%" />
</p>
<p align="center">
  <em>Landing page</em> · <em>Dashboard with stats and activity</em>
</p>

<p align="center">
  <img src="assets/screenshots/interview-setup.svg" alt="Interview Setup Wizard" width="49%" />
  <img src="assets/screenshots/live-interview.svg" alt="Live Interview Session" width="49%" />
</p>
<p align="center">
  <em>Setup wizard</em> · <em>Live interview session</em>
</p>

<p align="center">
  <img src="assets/screenshots/coding-interview.svg" alt="Coding Interview" width="49%" />
  <img src="assets/screenshots/evaluation-report.svg" alt="Evaluation Report" width="49%" />
</p>
<p align="center">
  <em>Coding interview with Monaco editor</em> · <em>Post-interview evaluation report</em>
</p>

---

## Architecture Overview

### High-Level Architecture

```mermaid
flowchart LR
    Browser[Browser] --> Next.js[Next.js 15 SSR]
    Browser --> WS[WebSocket]
    Next.js --> API[FastAPI REST]
    WS --> Sessions[Session Manager]
    
    subgraph Backend [FastAPI Modular Monolith]
        API
        Sessions
        Auth[Auth Module]
        Interview[Interview Module]
        Evaluation[Evaluation Pipeline]
        Reports[Reports Module]
        Workers[Background Workers]
        Sessions --> AI[AI Orchestrator]
        AI --> Provider[OpenAI / OpenRouter]
    end
    
    Backend --> DB[(PostgreSQL 17)]
    Backend --> Redis[(Redis 7)]
    Backend --> Storage[(S3 / MinIO)]
    
    Sessions --> WS
```

### Interview Lifecycle

```mermaid
stateDiagram-v2
    [*] --> IDLE: Create session
    IDLE --> PREPARING: Build AI context
    PREPARING --> ACTIVE: Generate first question
    ACTIVE --> PAUSED: User pauses
    PAUSED --> ACTIVE: User resumes
    ACTIVE --> COMPLETING: Last question answered
    COMPLETING --> COMPLETED: Wrap-up message
    COMPLETED --> ARCHIVED: Evaluation complete
    ACTIVE --> FAILED: Irrecoverable error
    ACTIVE --> TIMEOUT: Duration exceeded
    TIMEOUT --> COMPLETED: Force complete
```

### AI Evaluation Pipeline

```mermaid
flowchart LR
    Interview[Completed Interview] --> Transcript[Load Transcript]
    Transcript --> Prompt[Build Evaluation Prompt]
    Prompt --> GPT4[GPT-4o Structured Output]
    GPT4 --> Parse[Parse Response]
    Parse --> Scores[Dimension Scores]
    Parse --> Verdict[Hire Verdict]
    Parse --> Feedback[Strengths & Improvements]
    Scores --> DB[(PostgreSQL)]
    Verdict --> DB
    Feedback --> DB
```

### Directory Structure

```
tayari.ai/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── ai/                       # AI provider + realtime engine
│   │   │   ├── realtime/             # Session state machine, orchestrator, memory
│   │   │   ├── openai_provider.py    # OpenAI / OpenRouter integration
│   │   │   ├── mock_provider.py      # Development mock
│   │   │   └── code_review.py        # AI code review service
│   │   ├── core/                     # Config, DB, auth, storage, errors
│   │   ├── features/                 # Domain modules
│   │   │   ├── auth/                 # JWT, guards, password hashing
│   │   │   ├── interview/            # CRUD, setup wizard, file uploads
│   │   │   ├── sessions/             # WebSocket session persistence
│   │   │   ├── reports/              # Evaluation pipeline
│   │   │   ├── billing/              # Stripe stubs
│   │   │   ├── dashboard/            # Aggregated stats
│   │   │   ├── users/                # Admin user management
│   │   │   ├── voice/                # Deepgram STT
│   │   │   ├── code/                 # Code submissions
│   │   │   └── analytics/            # Usage analytics
│   │   ├── judge/                    # Code execution sandbox
│   │   └── workers/                  # APScheduler background tasks
│   └── web/                          # Next.js 15 frontend
│       ├── app/                      # App Router pages
│       ├── features/                 # Feature-sliced UI modules
│       ├── lib/                      # API client, utilities
│       └── components/               # Shared UI components
├── packages/
│   ├── prompts/                      # AI prompt templates (Markdown)
│   ├── types/                        # Zod schemas shared web↔api
│   ├── config/                       # ESLint + TypeScript configs
│   └── ui/                           # Shared React components
├── infrastructure/                   # Docker Compose, Traefik
├── .github/workflows/                # CI/CD pipelines
└── assets/screenshots/               # Documentation images
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript | SSR, client components, routing |
| **Styling** | Tailwind CSS v4, framer-motion | Utility-first CSS, animations |
| **State** | TanStack Query v5 | Server state, caching, mutations |
| **Backend** | Python 3.13, FastAPI 0.115, uvicorn | REST API + WebSocket |
| **ORM** | SQLAlchemy 2.0 (async), Alembic | Database access, migrations |
| **Database** | PostgreSQL 17 (via asyncpg) | Primary data store |
| **Cache** | Redis 7 | JWT blacklist, APScheduler job store |
| **Auth** | Custom JWT (RS256/HS256) | Token-based auth with refresh rotation |
| **AI** | OpenAI / OpenRouter (GPT-4o-mini, GPT-4o) | Interviewer + evaluator |
| **STT** | Deepgram (nova-3) | Speech-to-text |
| **Email** | Resend | Transactional email |
| **Storage** | S3-compatible (MinIO local / Supabase prod) | Resume/JD file storage |
| **Monitoring** | Sentry | Error tracking |
| **Background Jobs** | APScheduler (SQLAlchemyJobStore) | Async evaluation processing |
| **Code Execution** | Docker sandbox (subprocess fallback) | Isolated code runner (7 languages) |
| **CI/CD** | GitHub Actions | Lint, test, build, Docker |
| **Containerization** | Docker Compose, Traefik v3 | Local dev, reverse proxy |
| **Package Manager** | pnpm 9 (Node), uv (Python) | Monorepo dependency management |
| **Monorepo** | Turborepo 2 | Task orchestration |

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.13+ | Backend runtime |
| Node.js | 22+ | Frontend runtime |
| pnpm | 9+ | Node package manager |
| uv | Latest | Python package manager |
| Docker | 24+ | PostgreSQL, Redis, MinIO |
| Git | 2.40+ | Version control |

### Installation

```bash
# Clone the repository
git clone https://github.com/Mahnoor-Zaffar/Tayari.ai.git
cd Tayari.ai

# Start infrastructure (PostgreSQL, Redis, MinIO)
docker compose -f infrastructure/docker-compose.yml up -d

# Install Python dependencies
cd apps/api
uv sync --all-extras
uv run alembic upgrade head
uv run python scripts/seed.py
cd ../..

# Install Node dependencies
pnpm install

# Start development (API + Web concurrently)
pnpm dev
```

### Verify

| Service | URL |
|---------|-----|
| Web app | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| MinIO Console | http://localhost:9001 (tayari / tayari_dev) |

### Environment Variables

The API requires a `.env` file at `apps/api/.env`. Copy the template:

```bash
cp apps/api/.env.example apps/api/.env
```

Required variables for full functionality:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://tayari:tayari_dev@localhost:5432/tayari` | PostgreSQL connection |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection |
| `JWT_SECRET_KEY` | Yes | `change-me-in-production` | Token signing key |
| `JWT_ALGORITHM` | Yes | `RS256` | Signing algorithm |
| `OPENAI_API_KEY` | For AI | `""` | OpenAI / OpenRouter key |
| `RESEND_API_KEY` | For email | `""` | Transactional email |
| `DEEPGRAM_API_KEY` | For voice | `""` | Speech-to-text |
| `SENTRY_DSN` | No | `""` | Error tracking |
| `STORAGE_ENDPOINT` | For uploads | `""` | S3-compatible endpoint |
| `STORAGE_ACCESS_KEY` | For uploads | `""` | S3 access key |
| `STORAGE_SECRET_KEY` | For uploads | `""` | S3 secret key |

Frontend variables go in `apps/web/.env.local`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000/api/v1` | Backend URL |
| `NEXT_PUBLIC_SENTRY_DSN` | No | `""` | Frontend error tracking |
| `NEXT_PUBLIC_FF_*` | No | See `.env.example` | Feature flags |

### Running Specific Services

```bash
# Backend only
cd apps/api && uv run uvicorn main:app --reload --port 8000

# Frontend only
cd apps/web && pnpm dev

# Backend tests
cd apps/api && uv run pytest --ignore=tests/test_e2e_evaluation.py -v

# Frontend tests
pnpm --filter @tayari/web test

# Lint all
pnpm lint

# Typecheck all
pnpm typecheck
```

---

## API Overview

The API is organized into feature modules, each with its own router, schemas, service, and repository.

| Module | Prefix | Key Endpoints | Auth |
|--------|--------|---------------|------|
| **Auth** | `/auth` | `signup`, `login`, `logout`, `refresh`, `forgot-password`, `reset-password`, `verify-email` | No |
| **Interviews** | `/interviews` | CRUD, upload resume/JD, device check, difficulty estimate, config validation | Yes |
| **Sessions** | `/sessions` | WebSocket endpoint, pause/resume, reconnect, status | Yes |
| **Evaluations** | `/evaluations` | Trigger evaluation, list, get by interview ID | Yes |
| **Dashboard** | `/dashboard` | Aggregated stats, recent activity | Yes |
| **Users** | `/users` | Profile, admin user management | Yes |
| **Billing** | `/billing` | Stripe checkout stubs, subscription status | Yes |
| **Code** | `/code` | Code submissions, review | Yes |
| **Voice** | `/voice` | Deepgram transcription | Yes |
| **Analytics** | `/analytics` | Usage analytics | Yes |
| **Health** | `/health` | Service health check | No |

All responses follow a standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "request_id": "uuid"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "...",
    "details": []
  },
  "request_id": "uuid"
}
```

---

## Core Engineering Principles

### Feature-First Architecture

Each domain (`auth`, `interview`, `reports`, `sessions`, etc.) is a self-contained package with its own models, schemas, routes, services, repositories, and tests. Cross-feature dependencies are explicit and unidirectional.

```python
# Example: features/auth/ owns EVERYTHING for auth
features/auth/
├── routes.py          # FastAPI router
├── services.py        # Business logic
├── repositories.py    # Data access
├── schemas.py         # Pydantic request/response models
├── guard.py           # Auth guards (get_current_user, RoleChecker)
├── dependencies.py    # DI wiring
├── domain/            # Domain models
├── jwt/               # JWT sub-module (config, service, blacklist)
└── password/          # Password hashing sub-module
```

### Key Patterns

<details>
<summary><strong>Repository Pattern</strong> — Data access abstraction</summary>

```python
class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_email(self, email: str) -> User | None:
        ...

    async def create_user(self, data: dict) -> User:
        ...
```
</details>

<details>
<summary><strong>Service Layer</strong> — Business logic separated from HTTP</summary>

```python
class InterviewService:
    def __init__(self, repository: InterviewRepository) -> None:
        self._repo = repository

    async def create_interview(self, user_id: UUID, request: CreateInterviewRequest) -> InterviewResponse:
        # Validates free-tier limits, deduplicates, persists snapshot
        ...
```
</details>

<details>
<summary><strong>Dependency Injection</strong> — Testable components via FastAPI Depends</summary>

```python
async def get_interview_service(
    repository: InterviewRepository = Depends(get_interview_repository),
) -> InterviewService:
    return InterviewService(repository)
```
</details>

<details>
<summary><strong>Async-First</strong> — Non-blocking I/O throughout</summary>

All database operations use SQLAlchemy async session. AI provider calls, WebSocket message handling, and background tasks all use asyncio. The code execution queue uses `asyncio.Semaphore` for concurrency control.
</details>

<details>
<summary><strong>Modular Monolith</strong> — Microservice-ready boundaries without the operational cost</summary>

Feature modules are physically separated (own directory, own dependencies) but deployed as a single process. This gives clean boundaries for future extraction into microservices without paying the operational cost today.
</details>

---

## Testing

| Layer | Framework | Tests | What's tested |
|-------|-----------|-------|---------------|
| **Backend unit** | pytest + pytest-asyncio | 49 | Auth validation, session guards, state machine transitions, code judge output comparison, background worker error handling, email service HTML generation |
| **Backend integration** | pytest + httpx AsyncClient | — | Full request→DB→response for auth endpoints |
| **Frontend unit** | Vitest + React Testing Library | 92 | Component rendering, error/loading/empty states, form validation |
| **E2E** | Playwright | 9 | Auth flows (login, register, forgot-password), auth guard redirects |

### Running Tests

```bash
# All backend tests
cd apps/api && uv run pytest --ignore=tests/test_e2e_evaluation.py -v

# All frontend tests
pnpm --filter @tayari/web test

# E2E tests (requires running servers)
cd apps/web && pnpm test:e2e

# With coverage
cd apps/api && uv run pytest --cov --cov-report=term
```

### Pre-commit Hooks

On every `git commit`, the following run automatically via Husky + lint-staged:

1. **Prettier** — formats TypeScript, JavaScript, JSON, Markdown files
2. **Ruff** — lints and formats Python files (`ruff check --fix` + `ruff format`)
3. **pytest** — runs Python tests if any Python files changed

---

## Docker

### Development (docker-compose)

The `infrastructure/docker-compose.yml` provides all services for local development:

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `db` | postgres:17-alpine | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | Cache + job store |
| `minio` | minio/minio | 9000 (API), 9001 (Console) | S3-compatible storage |
| `api` | Build from `apps/api/Dockerfile.dev` | 8000 | FastAPI with hot-reload |
| `web` | Build from `apps/web/Dockerfile.dev` | 3000 | Next.js with hot-reload |

Start all services:

```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

### Production

Production Dockerfiles are available for both services:

| Service | Dockerfile | Base Image | Notes |
|---------|-----------|------------|-------|
| **API** | `apps/api/Dockerfile` | python:3.13-slim | Single-stage, `uv sync --no-dev`, HEALTHCHECK |
| **Web** | `apps/web/Dockerfile` | node:22-alpine | Multi-stage, Next.js build then minimal runner |

The `infrastructure/traefik/` directory contains a Traefik v3 reverse proxy configuration with automatic Let's Encrypt TLS for production deployments.

---

## CI/CD

### CI Pipeline (`.github/workflows/ci.yml`)

Triggers on push/PR to `main` and `feature/**` branches:

```mermaid
flowchart LR
    Push --> Lint[Lint & TypeCheck]
    Push --> JSTests[JS Tests]
    Push --> PyTests[Python Tests]
    Lint --> Build[Build]
    Build --> Deploy[Deploy]
    
    subgraph Lint [Lint & TypeCheck]
        Ruff[Ruff] --> ESLint[ESLint]
        ESLint --> MyPy[MyPy]
        MyPy --> TSC[TypeScript]
    end
    
    subgraph JSTests [JS Tests]
        Vitest[Vitest - 92 tests]
    end
    
    subgraph PyTests [Python Tests]
        Pytest[Pytest - 49 tests]
        Pg[PostgreSQL 17]
        Redis[Redis 7]
    end
```

| Job | Tools | Purpose |
|-----|-------|---------|
| `lint-and-typecheck` | ruff, mypy, eslint, tsc | Static analysis + type checking |
| `js-tests` | vitest | Frontend unit tests |
| `python-tests` | pytest (with PostgreSQL + Redis containers) | Backend tests |
| `build` | next build | Frontend production build + performance budget |
| `docker` | Docker Buildx | Production image build (API + Web) |

### Deployment

- **Railway**: Auto-deploys the API from `apps/api/Dockerfile` on push to `main`
- **Netlify**: Auto-deploys the frontend from `apps/web/` on push to `main`
- **Feature branches**: CI runs all checks but no deployment

---

## Roadmap

### Phase 1 ✅ (Current)

- [x] Email/password authentication with JWT refresh rotation
- [x] Three interview modalities (coding, system-design, behavioral)
- [x] Real-time AI interviewer with token streaming
- [x] Deepgram voice integration
- [x] Post-interview evaluation with dimension scoring
- [x] Dashboard with stats and activity tracking
- [x] Resume and job description upload
- [x] Session reconnection and resilience
- [x] Background evaluation via APScheduler
- [x] Docker Compose development environment
- [x] Sentry error monitoring
- [x] S3-compatible file storage
- [x] Redis-backed JWT blacklist
- [x] Admin user management
- [x] E2E test suite

### Phase 2 🔜

- [ ] Stripe billing integration
- [ ] Advanced analytics dashboard
- [ ] Interview replay (full session playback)
- [ ] Team / organization accounts
- [ ] Custom prompt management UI
- [ ] Multi-agent interview panels

### Phase 3 🚀

- [ ] Video interview support
- [ ] Real-time collaborative whiteboard
- [ ] Interview question bank with community contributions
- [ ] API for third-party integrations
- [ ] AI-powered interview question generation
- [ ] Performance benchmarking against industry standards

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. **Branch**: Create a feature branch from `main`
2. **CI**: All checks must pass before merging
3. **Commits**: Use conventional commit messages (`feat:`, `fix:`, `docs:`, `chore:`, etc.)
4. **Tests**: Add tests for new functionality
5. **Lint**: Run `pnpm lint` and fix any issues before pushing
6. **Review**: Open a pull request with a clear description of changes

### Development Workflow

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make changes, add tests, commit
git add .
git commit -m "feat: my feature description"

# Push and open a PR
git push -u origin feature/my-feature
```

### Code Style

- **Python**: Follow ruff rules (E, F, I, N, W, UP), line length 120, target Python 3.13
- **TypeScript/React**: ESLint with `@next/next` plugin, Prettier formatting
- **Imports**: Use absolute imports (`@/` for frontend, module paths for backend)
- **Typing**: Strict mode in both mypy (Python) and TypeScript

---

## License

This project is licensed under the MIT License.

---

<p align="center">
  Built with <a href="https://pnpm.io/">pnpm</a>, <a href="https://turbo.build/repo">Turborepo</a>, <a href="https://fastapi.tiangolo.com/">FastAPI</a>, and <a href="https://nextjs.org/">Next.js</a>
</p>
