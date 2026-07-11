# 01_Reverse_Engineering_Report

> **Project:** Tayari AI — AI Interview Platform  
> **Target:** Functional parity with DevInterview.ai  
> **Status:** v1.0 — Final  

---

# Document Information

| Field | Value |
|---|---|
| Version | 1.0 |
| Status | Final |
| Owner | Product Management |
| Audience | Engineering, Design, QA |

---

# 1. Executive Summary

DevInterview.ai is an AI-powered mock interview platform for software engineers. Users practice via live voice conversations with an AI interviewer across three formats: coding, system design, and behavioral. Each session is 30 minutes, followed by a scored evaluation.

This document is the definitive source of truth for building Tayari AI — covering every page, component, API, data model, edge case, and architectural decision discovered through reverse engineering.

## Objectives

- Achieve feature parity with DevInterview.ai
- Document every screen, route, modal, form, and validation
- Infer backend architecture, data model, and AI pipeline
- Produce implementation-ready requirements for a free-tier-friendly MVP

---

# 2. Target Platform Analysis

## 2.1 Product Overview

| Attribute | Detail |
|---|---|
| URL | https://devinterview.ai |
| Category | AI Mock Interview Platform |
| Target Users | Software engineers (junior to staff/lead) |
| Interview Types | Coding, System Design, Behavioral |
| Session Length | 30 minutes (+10 min grace period) |
| Voice | Live AI voice conversation |
| Pricing | $19.99/mo (50% off intro), $16.66/mo quarterly, $8.33/mo yearly |
| Free Tier | 1 free interview, no credit card |
| Languages (Coding) | Python, Java, C++, JavaScript, C# |
| Companies Tracked | 665+ |
| Concepts Tracked | 71 algorithms & data structures |

## 2.2 Unique Differentiators

- Live voice with trained AI interviewer (not a chat window)
- Interviewer asks clarifying questions, pushes back, gives hints
- Dedicated evaluation model (separate from interviewer)
- Progress tracking compared against previous sessions
- Real code editor with syntax highlighting and execution
- Excalidraw canvas for system design
- Company-specific problem matching

---

# 3. Site Map & Route Inventory

## 3.1 Public Routes

| Route | Purpose | Auth Required |
|---|---|---|
| `/` | Landing/marketing page | No |
| `/pricing` | Subscription plans and FAQ | No |
| `/companies` | Directory of 665+ tracked companies | No |
| `/companies/[slug]` | Company-specific questions page | No |
| `/concepts` | Directory of 71 algorithm concepts | No |
| `/concepts/[slug]` | Concept-specific questions page | No |
| `/about` | About + FAQ | No |
| `/blog` | Blog/articles | No |
| `/contact` | Contact form | No |

## 3.2 Authenticated Routes

| Route | Purpose |
|---|---|
| `/interview-setup` | Interview configuration wizard |
| `/interview/[id]/room` | Active interview room |
| `/my-interviews` | Interview history and past evaluations |
| `/my-interviews/[id]` | Single interview evaluation detail |
| `/settings` | User preferences |
| `/billing` | Subscription management |

## 3.3 Auth Routes

| Route | Purpose |
|---|---|
| `/login` | Sign in |
| `/signup` | Create account |
| `/forgot-password` | Password reset |
| `/reset-password` | Confirm password reset |

---

# 4. Interview Setup Wizard

## 4.1 Flow

The `/interview-setup` page is a multi-step form with dependent dropdowns:

```
Step 1: Interview Type
  ├── Coding
  ├── System Design
  └── Behavioral

Step 2: Company (665+)
  └── Search/filter with autocomplete

Step 3: Experience Level
  ├── Junior (0-2 years)
  ├── Mid/Senior (2-8 years)
  └── Staff/Lead (8+ years)
```

## 4.2 State Machine

| State | Description |
|---|---|
| LOADING | Initial page load, fetching companies/concepts |
| CONFIGURING | User is making selections |
| VALIDATING | Checking if questions exist for selected combo |
| READY | "Start Interview" button enabled |
| SUBMITTING | Creating interview session |
| ERROR | Network failure or no matching questions |

## 4.3 UI Components

- Type selector (3 cards with icons and descriptions)
- Company selector (searchable combobox with autocomplete)
- Experience level selector (3 pills/buttons)
- Company stats display (question count, difficulty breakdown)
- "Start Interview" CTA button
- Microphone permission prompt (first time)

## 4.4 Edge Cases

| Edge Case | Handling |
|---|---|
| Selected company has no questions | Show "This company isn't tracked yet" with fallback to general questions |
| Network failure on submit | Retry with exponential backoff, show error banner |
| Microphone permission denied | Show permission instruction modal, fallback to text-only |
| User navigates away mid-setup | Save partial state in localStorage, restore on return |
| Company search returns 0 results | Show "No companies found" with suggestion to browse all |
| Invalid combo (e.g. system design + junior) | Valid — all combos are valid |
| Session expires during setup | Redirect to login, preserve state in URL params |

---

# 5. Interview Room

## 5.1 Shared Layout (All Types)

```
┌──────────────────────────────────────────────┐
│  Header: Timer (30:00) · Company · Type · Lvl │
├──────────────────────────────────────────────┤
│                                              │
│         Main Workspace Area                  │
│     (Type-specific — see below)              │
│                                              │
├──────────────────────────────────────────────┤
│  Transcript / Chat Panel                     │
│  (scrollable, shows AI + user messages)      │
├──────────────────────────────────────────────┤
│  Controls: Mute · End · Settings             │
└──────────────────────────────────────────────┘
```

## 5.2 Coding Interview Room

| Element | Detail |
|---|---|
| Editor | Monaco Editor (lazy-loaded) |
| Languages | Python, Java, C++, JavaScript, C# |
| Execution | Pyodide (Python) + QuickJS (JS) — client-side WASM |
| Test Panel | Show test cases, pass/fail status, stdout |
| AI Behavior | Gives problem, watches code, hints when stuck, asks about complexity |
| Timer | 30:00 countdown, auto-submit at 0 |
| Grace Period | 10 minutes to test setup before interview starts |

### Edge Cases — Coding

| Edge Case | Handling |
|---|---|
| WASM fails to load | Show error, fallback to text-only coding |
| User submits empty code | Prompt "Did you want to submit your solution?" |
| Code causes infinite loop | WASM timeout after 5s, kill execution |
| Browser tab loses focus | Pause timer, show reconnection overlay |
| Connection drops mid-interview | Reconnect WebSocket, restore state from server |
| User pastes external code | No restriction — AI evaluation will detect |

## 5.3 System Design Interview Room

| Element | Detail |
|---|---|
| Canvas | Excalidraw (open source, fully client-side) |
| AI Behavior | Asks to design a system, challenges trade-offs: "Why a queue there?" |
| Shared Canvas | Canvas state synced via WebSocket (for future multi-user) |
| Timer | 30:00 |

## 5.4 Behavioral Interview Room

| Element | Detail |
|---|---|
| UI | Transcript-only panel with voice |
| AI Behavior | Asks situational questions, STAR follow-ups, digs deeper |
| Timer | 30:00 |

## 5.5 Voice Pipeline (MVP)

```text
User speaks into microphone
       │
       ▼
Browser records 5-10 second audio chunk
       │
       ▼
Web Speech API (SpeechRecognition) transcribes chunk
       │
       ▼
Transcription sent to AI via REST/WebSocket
       │
       ▼
AI generates response text (GPT-4o-mini)
       │
       ▼
Speech Synthesis API (speechSynthesis.speak) plays response
       │
       ▼
Loop until interview ends
```

### Voice States

| State | Description |
|---|---|
| LISTENING | Browser recording audio |
| PROCESSING | Audio chunk being transcribed |
| THINKING | AI generating response |
| SPEAKING | TTS playing AI response |
| IDLE | Waiting for user to start speaking |
| ERROR | Microphone or API failure |

### Edge Cases — Voice

| Edge Case | Handling |
|---|---|
| Browser doesn't support Web Speech API | Show unsupported browser warning, fallback to text chat |
| User is silent for 30s | AI prompts "Are you still there?" |
| Background noise triggers false transcription | Implement voice activity detection (VAD) |
| TTS interrupted by user speaking | Stop TTS, listen to user |
| Audio chunk fails to transcribe | Retry once, then show "I didn't catch that" message |

---

# 6. Evaluation System

## 6.1 Scoring Dimensions

### Coding

| Dimension | Weight | What it measures |
|---|---|---|
| Technical Communication | 25% | Clarity of explanation, narrating approach |
| Problem Solving | 30% | Algorithm choice, edge case handling, optimization |
| Code Quality | 25% | Readability, correctness, language idioms |
| Language Proficiency | 20% | Syntax fluency, standard library usage |

### System Design

| Dimension | Weight | What it measures |
|---|---|---|
| Requirements Gathering | 20% | Clarifying functional + non-functional reqs |
| Architecture | 30% | Component breakdown, data flow |
| Trade-off Analysis | 30% | Justifying decisions, comparing alternatives |
| Communication | 20% | Clarity of explanation |

### Behavioral

| Dimension | Weight | What it measures |
|---|---|---|
| Structure (STAR) | 30% | Situation → Task → Action → Result |
| Relevance | 25% | Answer matches question asked |
| Specificity | 25% | Concrete details, not generic |
| Impact | 20% | Measurable outcomes, learnings |

## 6.2 Evaluation Pipeline

```text
Interview ends
       │
       ▼
Full transcript + code (if coding) sent to GPT-4o
       │
       ▼
AI evaluator generates:
  - Dimension scores (1-5)
  - Overall score (1-5)
  - Hire/No-hire recommendation
  - Strengths (2-3 bullet points)
  - Areas to improve (2-3 bullet points)
  - Specific moment references
  - Delta vs previous session
       │
       ▼
Evaluation stored in PostgreSQL
       │
       ▼
User sees evaluation on interview complete screen
       │
       ▼
Available in /my-interviews history
```

## 6.3 Evaluation States

| State | Description |
|---|---|
| PENDING | Interview ended, evaluation queued |
| GENERATING | AI evaluation in progress |
| COMPLETE | Evaluation ready |
| FAILED | Evaluation generation failed |

---

# 7. AI Architecture

## 7.1 Models

| Model | Role | Provider | Cost Tier |
|---|---|---|---|
| GPT-4o-mini | Interviewer (real-time) | OpenAI | Cheap (~$0.15/M in) |
| GPT-4o | Evaluator (post-session) | OpenAI | Expensive (~$2.50/M in) |

## 7.2 Prompt Architecture

### Interviewer System Prompt Structure

```
System prompt includes:
  - Persona definition (senior big tech engineer)
  - Interview type rules
  - Company-specific style
  - Difficulty calibration
  - HINT: Only give hints after user asks or is stuck 30s
  - NO: Give away the answer
  - Evaluation: Never do evaluation during interview
  - Token budget: ~$0.10 max per interview
```

### Evaluator System Prompt Structure

```
  - Dimension definitions and scoring rubrics
  - Company-specific expectations
  - Level-specific expectations
  - Delta calculation logic
  - Hire/No-hire thresholds
```

## 7.3 Token Budget Strategy

| Interview Component | Model | Est. Tokens | Est. Cost |
|---|---|---|---|
| Interviewer (30 min) | GPT-4o-mini | 100K-300K | $0.06-0.18 |
| Evaluation | GPT-4o | 10K-20K | $0.03-0.05 |
| **Total per interview** | | | **$0.09-0.23** |

**Cost cap:** Hard limit of $0.30/interview. If exceeded, downgrade to mini for remainder.

---

# 8. API Surface

## 8.1 REST Endpoints

### Authentication

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/login` | Sign in |
| POST | `/api/auth/logout` | Sign out |
| POST | `/api/auth/refresh` | Refresh JWT |
| POST | `/api/auth/forgot-password` | Send reset email |
| POST | `/api/auth/reset-password` | Confirm reset |

### Users

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/users/me` | Get current user profile |
| PATCH | `/api/users/me` | Update profile |
| DELETE | `/api/users/me` | Delete account |

### Interviews

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/interviews` | Create new interview session |
| GET | `/api/interviews` | List user's interviews (paginated) |
| GET | `/api/interviews/:id` | Get interview details |
| PATCH | `/api/interviews/:id/status` | Update interview status |
| POST | `/api/interviews/:id/evaluation` | Trigger evaluation |
| GET | `/api/interviews/:id/evaluation` | Get evaluation |

### Companies

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/companies` | List companies (paginated, searchable) |
| GET | `/api/companies/:slug` | Company detail + question stats |
| GET | `/api/companies/:slug/questions` | Questions for a company |

### Concepts

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/concepts` | List concepts |
| GET | `/api/concepts/:slug` | Concept detail + question count |

### Billing

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/billing/create-checkout` | Stripe checkout session |
| GET | `/api/billing/portal` | Stripe customer portal |
| GET | `/api/billing/subscription` | Current subscription status |
| POST | `/api/billing/webhook` | Stripe webhook receiver |

## 8.2 WebSocket Events (Interview Room)

### Client → Server

| Event | Payload | Description |
|---|---|---|
| `interview:join` | `{ interviewId }` | Join room |
| `interview:leave` | `{ interviewId }` | Leave room |
| `voice:chunk` | `{ audio: Blob }` | Audio chunk for transcription |
| `voice:transcript` | `{ text: string }` | Speech-to-text result (browser-side) |
| `code:change` | `{ code: string, language: string }` | Code editor content |
| `code:run` | `{ code: string, language: string }` | Execute code |
| `canvas:update` | `{ elements: Element[] }` | Excalidraw canvas state |
| `interview:pause` | `{}` | Pause timer |
| `interview:resume` | `{}` | Resume timer |
| `interview:end` | `{}` | End interview early |

### Server → Client

| Event | Payload | Description |
|---|---|---|
| `interview:state` | `{ status, timer }` | Full interview state |
| `ai:message` | `{ text: string }` | AI response text |
| `ai:thinking` | `{}` | AI is generating |
| `voice:response` | `{ audio: Blob }` | TTS audio chunk |
| `code:result` | `{ output, passed, error }` | Code execution result |
| `timer:tick` | `{ remaining: number }` | Timer sync |
| `interview:complete` | `{ interviewId }` | Interview ended |
| `error` | `{ code, message }` | Error notification |

## 8.3 WebRTC Signaling

For future OpenAI Realtime API integration:

| Event | Description |
|---|---|
| `webrtc:offer` | SDP offer from client |
| `webrtc:answer` | SDP answer from server |
| `webrtc:ice-candidate` | ICE candidate exchange |

---

# 9. Data Model

## 9.1 Core Entities

```
users
├── id: UUID (PK)
├── email: string (unique)
├── password_hash: string
├── display_name: string
├── experience_level: enum(junior, mid, senior, staff)
├── avatar_url: string?
├── email_verified: boolean
├── created_at: timestamp
├── updated_at: timestamp

interviews
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── type: enum(coding, system-design, behavioral)
├── company: string
├── experience_level: enum(junior, mid, senior, staff)
├── language: string? (coding only)
├── status: enum(pending, active, completed, cancelled)
├── timer_remaining: integer (seconds)
├── transcript: jsonb[]
├── ai_messages: jsonb[]
├── created_at: timestamp
├── started_at: timestamp?
├── completed_at: timestamp?
├── cancelled_at: timestamp?

evaluations
├── id: UUID (PK)
├── interview_id: UUID (FK → interviews)
├── overall_score: decimal(3,1)
├── dimension_scores: jsonb
├── hire_verdict: enum(hire, no-hire, lean-hire, lean-no-hire)
├── strengths: text[]
├── improvements: text[]
├── delta_vs_last: decimal(3,1)?
├── raw_evaluation: text
├── model: string
├── status: enum(pending, generating, complete, failed)
├── created_at: timestamp

companies
├── id: UUID (PK)
├── name: string
├── slug: string (unique)
├── question_count: integer
├── difficulty_breakdown: jsonb
├── created_at: timestamp

questions
├── id: UUID (PK)
├── title: string
├── description: text
├── type: enum(coding, system-design, behavioral)
├── difficulty: enum(easy, medium, hard)
├── concepts: UUID[] (FK → concepts)
├── companies: UUID[] (FK → companies)
├── created_at: timestamp

concepts
├── id: UUID (PK)
├── name: string
├── slug: string (unique)
├── question_count: integer
├── created_at: timestamp

subscriptions
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── stripe_subscription_id: string
├── status: enum(active, canceled, past_due, incomplete)
├── plan: enum(monthly, quarterly, yearly)
├── current_period_start: timestamp
├── current_period_end: timestamp
├── created_at: timestamp
├── updated_at: timestamp

billing_events
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── event_type: string
├── stripe_event_id: string (unique)
├── data: jsonb
├── created_at: timestamp
```

## 9.2 Key Indexes

| Table | Index | Purpose |
|---|---|---|
| interviews | `(user_id, created_at DESC)` | Fast history queries |
| interviews | `(status, created_at)` | Active session lookup |
| questions | `(type, difficulty)` | Filter by type |
| questions_concepts | `(concept_id, question_id)` | Concept join |
| questions_companies | `(company_id, question_id)` | Company join |
| subscriptions | `(user_id)` | One subscription per user |
| billing_events | `(stripe_event_id)` | Idempotency |

---

# 10. Edge Cases & Error States (Cross-Cutting)

## 10.1 Loading States

| Component | Skeleton / Spinner |
|---|---|
| Interview setup page | Shimmer cards for type selector |
| Company list | Skeleton list with 10 items |
| Interview history | Skeleton table rows |
| Evaluation report | Full-page skeleton with score placeholders |
| Company/concept pages | Skeleton cards for question list |

## 10.2 Empty States

| Page | Empty State Message |
|---|---|
| My Interviews (no interviews) | "You haven't taken any interviews yet. Start your first one!" + CTA |
| My Interviews (no evaluations) | "Your evaluation is being generated. Check back shortly." |
| Company search (no results) | "No companies found matching your search." + suggestion |
| Company questions (none) | "We haven't tracked questions for this company yet. Try a different one." |
| Billing (no subscription) | "You're on the free tier. Upgrade for unlimited interviews." |

## 10.3 Error States

| Scenario | UX |
|---|---|
| API 401 | Redirect to login with message |
| API 403 | Show "You don't have access to this feature" with upgrade CTA |
| API 429 | Show "Too many requests. Please wait." with retry countdown |
| API 500 | Show "Something went wrong" with retry button |
| Network offline | Show persistent banner "You're offline" |
| WebSocket disconnect | Show overlay "Reconnecting..." with spinner |
| Browser too old | Show warning banner with browser upgrade link |
| Microphone blocked | Show permission instructions with test button |
| Payment failed | Show specific error from Stripe, offer retry |

---

# 11. Architecture & Stack (Final)

## 11.1 Tech Stack

| Layer | Technology | Cost |
|---|---|---|
| Frontend | Next.js 15 + React 19 + TypeScript | Free |
| UI | Tailwind CSS v4 + shadcn/ui | Free |
| Forms | React Hook Form + Zod | Free |
| State / Data | TanStack Query | Free |
| Backend | FastAPI + SQLAlchemy 2 + Alembic | Free |
| Database | PostgreSQL 17 (Neon free tier) | Free |
| Storage | Cloudflare R2 | Free (free tier) |
| Auth | Custom JWT (FastAPI + python-jose) | Free |
| Voice (MVP) | Web Speech API + Speech Synthesis API | Free |
| Voice (future) | OpenAI Realtime API | Paid |
| AI Interviewer | GPT-4o-mini | ~$0.06-0.18/interview |
| AI Evaluator | GPT-4o | ~$0.03-0.05/interview |
| Code Execution | Pyodide + QuickJS (client-side WASM) | Free |
| Email | Resend | Free (500/mo) |
| Monitoring | Sentry | Free |
| Analytics | PostHog | Free |
| Payments | Stripe | Per-transaction fee |
| Background Jobs | APScheduler (MVP) → Celery + Redis (later) | Free |
| CI/CD | GitHub Actions | Free |

## 11.2 Architecture Diagram

```
                    Cloudflare CDN
                           │
                  ┌────────┴────────┐
                  │                 │
            Vercel Hobby      Railway / Fly.io
           (Next.js app)      (FastAPI backend)
                  │                 │
                  └────────┬────────┘
                           │
                    FastAPI (modular monolith)
                           │
              ┌────────────┼────────────┐
              │            │            │
         Neon PG 17    Cloudflare R2   APScheduler
         (primary DB)  (objects)       (bg tasks)
              │
         Pyodide + QuickJS
         (client-side WASM)

         WebSocket (interview events)
         WebRTC   (audio, post-MVP)
```

## 11.3 Modular Monolith Structure (apps/api/)

```text
apps/api/
├── main.py                  # FastAPI app factory
├── core/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── security.py          # JWT encode/decode, password hashing
│   └── dependencies.py      # FastAPI DI (get_db, get_current_user)
├── routers/
│   ├── auth.py              # /api/auth/*
│   ├── users.py             # /api/users/*
│   ├── interviews.py        # /api/interviews/*
│   ├── companies.py         # /api/companies/*
│   ├── concepts.py          # /api/concepts/*
│   └── billing.py           # /api/billing/*
├── services/
│   ├── auth.py              # Auth business logic
│   ├── interview.py         # Interview lifecycle
│   ├── evaluation.py        # Evaluation orchestration
│   ├── ai.py                # AI client wrapper
│   ├── voice.py             # Voice pipeline (future)
│   └── billing.py           # Stripe integration
├── models/
│   ├── user.py
│   ├── interview.py
│   ├── evaluation.py
│   ├── question.py
│   ├── company.py
│   ├── concept.py
│   ├── subscription.py
│   └── billing_event.py
├── schemas/
│   ├── auth.py              # Pydantic request/response models
│   ├── user.py
│   ├── interview.py
│   ├── evaluation.py
│   └── billing.py
└── workers/
    └── evaluation.py        # APScheduler jobs
```

---

# 12. Performance Budgets

| Metric | Target | Measurement |
|---|---|---|
| Voice chunk turnaround (STT→AI→TTS) | <2s P95 | Browser performance API |
| Code execution (Python, WASM) | <500ms P95 | Client-side timing |
| Code execution (JS, WASM) | <300ms P95 | Client-side timing |
| Interview setup page load (LCP) | <2s P90 | Lighthouse |
| My Interviews page load | <1.5s P90 | Lighthouse |
| Evaluation generation (first token) | <3s | Server timing |
| Evaluation generation (complete) | <30s P95 | Server timing |
| WebSocket reconnection | <2s | Client-side timing |
| API P95 latency (non-AI) | <200ms | Sentry |
| API P95 latency (AI calls) | <5s | Sentry |

---

# 13. Performance Optimizations (Day 1)

| Optimization | Where | Why |
|---|---|---|
| Server Components for static pages | Next.js | Zero JS for marketing pages |
| Lazy load Monaco Editor | Interview Room | Monaco is ~3MB, only load on coding type |
| Stream AI responses | WebSocket | Token-by-token for perceived speed |
| Incremental rendering | Next.js ISR | Company/concept pages, rebuild on data change |
| Image optimization | Next.js Image | CDN-served, WebP, responsive sizes |
| HTTP/2 on Cloudflare | Edge | Multiplexing for many assets |
| Connection pooling | FastAPI + SQLAlchemy | PgBouncer-style pooling (Neon built-in) |
| Optimistic UI updates | TanStack Query | Immediately show UI, reconcile after API |
| Idempotent API design | FastAPI | Safe retry on network failure |
| Virtualized tables | Interview History | Only render visible rows |
| CDN for static assets | Cloudflare | Edge-cached JS, CSS, images |
| WASM code execution (no server round-trip) | Pyodide/QuickJS | Eliminates network hop for code runs |

---

# 14. Deliverables Checklist

- [x] Reverse Engineering Report (this document)
- [ ] 02_PRD.md — Product Requirements Document
- [ ] 03_SRS.md — Software Requirements Specification
- [ ] 04_UI_Specification.md — UI Component Library & Design Tokens
- [ ] 05_Database_Design.md — ERD, Indexes, Migration Strategy
- [ ] 06_API_Specification.md — Full OpenAPI Contract
- [ ] 07_AI_Architecture.md — Prompt Design, Model Selection, Token Budget
- [ ] 08_Testing_Strategy.md — Unit, Integration, E2E, Voice Testing
- [ ] Sprint Backlog — Phase 1 MVP Tasks

---

**Revision History**

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-07-12 | Initial scaffold |
| 1.0 | 2026-07-12 | Full reverse engineering report with architecture, stack, data model |
