# 02_PRD — Product Requirements Document

> **Project:** Tayari AI — AI Interview Platform  
> **Version:** 1.0  
> **Status:** Final  
> **Owner:** Product Management  

---

# 1. Purpose

Build a production-ready AI-powered mock interview platform that achieves feature parity with DevInterview.ai, using original implementation and branding, optimized for free-tier infrastructure during MVP phase.

---

# 2. Product Vision

An AI-powered interview preparation platform where software engineers practice with live voice conversations across coding, system design, and behavioral formats — receiving detailed evaluations and progress tracking — all at a fraction of the cost of human mock interviews.

---

# 3. Objectives

| Objective | Success Metric | Target |
|---|---|---|
| User can complete a full interview loop | Interview completion rate | >70% |
| Users perceive AI as realistic | Session repeat rate | >40% within 7 days |
| Free-tier infrastructure sustains 500 interviews/mo | Monthly infra cost (excl AI) | <$5 |
| AI cost per interview | Average cost per session | <$0.25 |
| Subscription conversion | Free → paid conversion | >5% |
| Voice interaction feels natural | Voice latency P95 | <2s |

---

# 4. Target Users

| Persona | Description | Priority |
|---|---|---|
| Job-seeking SWE | Actively interviewing, needs realistic practice | P0 |
| Career switcher | Non-CS background, needs repetition | P1 |
| New grad | Little interview experience, needs format familiarity | P1 |
| Senior engineer | Prepping for staff/principal loops | P1 |
| International candidate | Needs practice with English technical communication | P2 |

---

# 5. Features by Priority

## 5.1 Phase 1 — MVP (Ship in 6-8 weeks)

### P0 — Must Have

| Feature | Description |
|---|---|
| Authentication | Email/password signup, login, JWT session, password reset |
| Interview Setup | 3-step wizard: type → company → experience level |
| Coding Interview Room | Monaco editor, Pyodide/QuickJS execution, test panel, timer, transcript |
| Voice (pseudo-realtime) | Browser Speech API recording (5-10s chunks), transcription, AI response, TTS playback |
| AI Interviewer (Coding) | GPT-4o-mini, company-specific problems, adaptive hints, 30-min sessions |
| Post-Interview Evaluation | GPT-4o evaluation, scored dimensions, hire verdict, improvement areas |
| Interview History | List of past interviews with scores, ability to revisit evaluations |
| Landing Page | Product overview, social proof, CTA to start free interview |
| Pricing Page | 3 tiers (monthly/quarterly/yearly), FAQ |
| Stripe Checkout | Free first interview → subscribe for unlimited |
| Subscription Management | Status, cancel, change plan (Stripe customer portal) |

### P1 — Should Have

| Feature | Description |
|---|---|
| Company directory | Browse 665+ companies with question counts |
| Company detail page | Questions tagged to each company |
| Concept directory | Browse 71 algorithm concepts |
| Concept detail page | Questions tagged to each concept |
| Basic profile settings | Name, email, password change |
| Email verification | Resend-powered verification flow |
| Progress tracking | Score delta vs previous session |

### P2 — Nice to Have (Post-MVP)

| Feature | Description |
|---|---|
| System Design interviews | Excalidraw canvas integration |
| Behavioral interviews | STAR-structured voice sessions |
| Browser compatibility fallback | Text-only mode for unsupported browsers |
| Blog | Marketing content |
| Contact form | User inquiries |

## 5.2 Phase 2 — Post-MVP (Months 3-6)

| Feature | Priority |
|---|---|
| OpenAI Realtime API (true realtime voice) | P0 |
| System Design interview type | P0 |
| Behavioral interview type | P0 |
| Admin dashboard (users, interviews, revenue) | P1 |
| Resume upload for personalized questions | P1 |
| Job description upload | P1 |
| Payment history page | P1 |
| Dark mode | P2 |
| Download evaluation as PDF | P2 |
| Celery + Redis for background jobs | P1 |

---

# 6. Functional Requirements

## FR-01: Authentication

| ID | Requirement |
|---|---|
| FR-01.1 | User can sign up with email and password |
| FR-01.2 | User can sign in with email and password |
| FR-01.3 | User can sign out |
| FR-01.4 | JWT expires after 24h; refresh token rotates |
| FR-01.5 | User can request password reset via email |
| FR-01.6 | User can reset password with a valid token |
| FR-01.7 | Email verification is sent on signup (not blocking) |
| FR-01.8 | Session is preserved across page refresh (httpOnly cookie) |
| FR-01.9 | Rate limit: 5 login attempts per minute per IP |

## FR-02: Interview Setup

| ID | Requirement |
|---|---|
| FR-02.1 | User selects interview type from 3 options (coding, system-design, behavioral) |
| FR-02.2 | User selects company from searchable list of 665+ |
| FR-02.3 | User selects experience level (junior, mid/senior, staff/lead) |
| FR-02.4 | For coding interviews, user selects language (Python, Java, C++, JavaScript, C#) |
| FR-02.5 | System validates that questions exist for selected combination |
| FR-02.6 | System requests microphone permission before starting |
| FR-02.7 | "Start Interview" button is disabled until all required fields are filled |
| FR-02.8 | User can start free interview without subscription |
| FR-02.9 | Subscribed users see remaining interview count (unlimited for paid) |
| FR-02.10 | Form state persists if user navigates away and returns (localStorage) |

## FR-03: Interview Room (Coding)

| ID | Requirement |
|---|---|
| FR-03.1 | Editor loads with problem description in the target language |
| FR-03.2 | AI interviewer greets the user and explains the problem via voice |
| FR-03.3 | AI interviewer listens (via browser speech recognition) and responds (via TTS) |
| FR-03.4 | Full transcript of the conversation is displayed in real-time |
| FR-03.5 | Timer counts down from 30:00; flashes red at 5:00 remaining |
| FR-03.6 | User can run code against test cases (Pyodide/QuickJS) |
| FR-03.7 | Test results show pass/fail per case, stdout, and any errors |
| FR-03.8 | AI can see the user's code and discuss it |
| FR-03.9 | User can mute/unmute microphone |
| FR-03.10 | User can end interview early |
| FR-03.11 | Auto-submit when timer reaches 0 |
| FR-03.12 | 10-minute grace period before interview officially starts |
| FR-03.13 | Connection drops: WebSocket reconnects, state restored |
| FR-03.14 | WASM execution timeout: 5 seconds, auto-kill infinite loops |

## FR-04: Evaluation

| ID | Requirement |
|---|---|
| FR-04.1 | Evaluation is generated asynchronously after interview ends |
| FR-04.2 | Evaluation shows overall score (1-5) with hire/no-hire verdict |
| FR-04.3 | Dimension scores are shown with labels and descriptions |
| FR-04.4 | Strengths and areas for improvement are listed (2-3 each) |
| FR-04.5 | Delta vs previous session is shown (if previous exists) |
| FR-04.6 | Full interview transcript is replayable |
| FR-04.7 | Evaluation is accessible from /my-interviews history |
| FR-04.8 | Failed evaluations show retry option |

## FR-05: Billing & Subscriptions

| ID | Requirement |
|---|---|
| FR-05.1 | New users get 1 free interview without credit card |
| FR-05.2 | 3 subscription plans: monthly ($19.99), quarterly ($49.99), yearly ($99.99) |
| FR-05.3 | Stripe Checkout handles payment collection |
| FR-05.4 | Stripe Customer Portal handles subscription management |
| FR-05.5 | Webhook receiver idempotently processes stripe events |
| FR-05.6 | 14-day money-back guarantee |
| FR-05.7 | Cancel anytime, access until end of billing period |
| FR-05.8 | Free users see upgrade prompts after using free interview |

## FR-06: Interview History

| ID | Requirement |
|---|---|
| FR-06.1 | List shows all past interviews sorted by date (newest first) |
| FR-06.2 | Each item shows: type, company, date, score, status |
| FR-06.3 | User can click to view full evaluation |
| FR-06.4 | Paginated (20 per page, virtualized) |
| FR-06.5 | Empty state with CTA to start first interview |
| FR-06.6 | Filter by type and date range |
| FR-06.7 | Score trends shown (optional visual sparkline) |

---

# 7. Non-Functional Requirements

## NFR-01: Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-01.1 | Voice chunk turnaround | <2s P95 |
| NFR-01.2 | Code execution (Python WASM) | <500ms P95 |
| NFR-01.3 | Page load (marketing pages) | <2s LCP |
| NFR-01.4 | API response (non-AI) | <200ms P95 |
| NFR-01.5 | Evaluation generation | first token <3s, complete <30s |
| NFR-01.6 | WebSocket reconnection | <2s |

## NFR-02: Availability & Reliability

| ID | Requirement |
|---|---|
| NFR-02.1 | Uptime target: 99.5% (excluding planned maintenance) |
| NFR-02.2 | Graceful degradation: voice fails → text fallback |
| NFR-02.3 | Idempotent Stripe webhook processing |
| NFR-02.4 | Auto-retry with backoff for transient AI failures |

## NFR-03: Security

| ID | Requirement |
|---|---|
| NFR-03.1 | Passwords hashed with bcrypt (cost factor 12) |
| NFR-03.2 | JWTs signed with RS256, 24h expiry |
| NFR-03.3 | All API calls over HTTPS |
| NFR-03.4 | Rate limiting on auth endpoints |
| NFR-03.5 | CORS restricted to frontend domain |
| NFR-03.6 | API keys never exposed client-side |
| NFR-03.7 | Stripe keys stored server-side only |

## NFR-04: Accessibility

| ID | Requirement | Standard |
|---|---|---|
| NFR-04.1 | All interactive elements keyboard-navigable | WCAG 2.1 A |
| NFR-04.2 | Color contrast ratio >= 4.5:1 for text | WCAG 2.1 AA |
| NFR-04.3 | Screen reader labels on all form inputs | WCAG 2.1 A |
| NFR-04.4 | Focus indicators visible on all elements | WCAG 2.1 AA |

## NFR-05: Browser Support

| ID | Requirement |
|---|---|
| NFR-05.1 | Chrome, Firefox, Safari, Edge (last 2 major versions) |
| NFR-05.2 | Web Speech API required for voice (Chrome recommended) |
| NFR-05.3 | Graceful fallback to text chat on unsupported browsers |
| NFR-05.4 | Mobile browser: functional but not optimized (v1) |

---

# 8. Constraints

| Constraint | Detail |
|---|---|
| AI budget | Hard cap of $0.30/interview in model costs |
| Database | Neon free tier: 500MB, 100k compute credits |
| Storage | Cloudflare R2 free tier: 10GB |
| Email | Resend free tier: 500 emails/month |
| Frontend hosting | Vercel Hobby: 100GB bandwidth, 6000 build min/mo |
| Code execution | Client-side WASM only. No Java/C++/C# (pending paying users) |
| Background jobs | APScheduler in-process. No Redis/Celery until needed |
| Voice quality | Browser Speech API (limited vs Realtime API). Upgrade later |

---

# 9. Success Metrics

| Metric | How to Measure | Phase 1 Target |
|---|---|---|
| Interview completion rate | % started vs completed | >70% |
| Free interview → signup conversion | % landing visitors who signup | >3% |
| Free → paid conversion | % signed up who subscribe | >5% |
| Weekly active users | Unique users with ≥1 interview/week | >100 (target) |
| NPS-like score | Post-interview survey (1-5) | >4.0 |
| Average session duration | Minutes from start to end | >20 min |
| Interview retake rate | % users with >1 interview | >40% |
| AI cost per interview | Total AI spend / total interviews | <$0.25 |

---

# 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| AI cost overruns | High | Medium | Token budget per interview, alerting at 80% threshold, auto-downgrade model |
| Browser Speech API unreliable | Medium | Medium | Text fallback, prompt users to use Chrome |
| WASM limitations (no Java/C++/C#) | Medium | High | Document in UI, add Piston when paying users request it |
| WebSocket instability on free hosting | Medium | Medium | Railway over Render for persistent connections |
| Stripe integration complexity | Low | Low | Use Stripe Checkout + Customer Portal (minimal custom code) |
| Low interview quality from 4o-mini | Medium | Medium | A/B test mini vs 4o for interviewer, evaluate switch at scale |
| Neon free tier DB limits | Low | Medium | Monitor compute credits, index optimization, archive old interviews |
| Low conversion rate | High | Medium | Improve evaluation quality, add email reminders, referral program |

---

# 11. Out of Scope (Phase 1)

- System design interview type (Excalidraw canvas)
- Behavioral interview type
- OpenAI Realtime API (true realtime voice)
- Resume / job description upload
- Admin dashboard
- Mobile app
- ATS integrations
- Recruiter marketplace
- Multi-language support (UI)
- Whiteboard / diagram collaboration
- Team/enterprise accounts
- SSO / OAuth providers (Google, GitHub)
- PDF report downloads
- Dark mode

---

# 12. Future Versions (Phase 2+)

| Version | Features |
|---|---|
| v1.1 | System design interviews, behavioral interviews |
| v1.2 | OpenAI Realtime API, reduced voice latency |
| v1.3 | Admin dashboard, resume parsing for personalized questions |
| v1.4 | Dashboard analytics, progress charts, PDF exports |
| v2.0 | Celery + Redis, server-side Piston (Java/C++/C#), dark mode |
| v2.1 | Team accounts, recruiter dashboard |
| v2.2 | Multi-agent interviews, custom prompt builder |

---

# 13. Technical Architecture Summary

See `01_Reverse_Engineering_Report.md` (Section 11) for full architecture.

## 13.1 High-Level Architecture

```
Frontend (Next.js 15, Vercel Hobby)
       │
       ├── REST API ──→ FastAPI (modular monolith, Railway/Fly.io)
       │                     │
       │                     ├── Neon PostgreSQL 17
       │                     ├── Cloudflare R2
       │                     └── APScheduler (bg tasks)
       │
       ├── WebSocket ──→ FastAPI (real-time interview events)
       │
       └── WebRTC ──→ Browser APIs (voice, MVP)
                      │
                      ├── Web Speech API (STT)
                      └── Speech Synthesis API (TTS)
```

## 13.2 Key Technical Decisions

| Decision | Rationale |
|---|---|
| Modular monolith (not microservices) | Faster to ship, easier to refactor when real bottlenecks are known |
| Client-side WASM for code execution | Zero server cost, eliminates network latency for code runs |
| Browser Speech API for voice | $0 cost vs OpenAI Realtime API ($0.06/min) |
| Custom JWT (not Better Auth / Clerk) | Better Auth is Next.js-only; custom JWT works cleanly with FastAPI |
| APScheduler (not Celery) | No Redis dependency for MVP. Upgrade when queue volume justifies it |
| Neon (not Supabase) | Dedicated Postgres experience, free tier is generous |
| Manual Zod + Pydantic (not OpenAPI codegen) | Simple, no build step, full control over type definitions |

---

# 14. Project Structure

```
ai-interview-platform/
├── apps/
│   ├── web/                    # Next.js 15 (App Router)
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── public/
│   └── api/                    # FastAPI modular monolith
│       ├── main.py
│       ├── core/
│       ├── routers/
│       ├── services/
│       ├── models/
│       ├── schemas/
│       └── workers/
├── packages/
│   ├── ui/                     # shadcn components, shared React
│   ├── types/                  # Zod schemas + Pydantic models
│   ├── config/                 # ESLint, TS config, constants
│   └── prompts/                # AI system prompts (version controlled)
├── infrastructure/
│   ├── docker-compose.yml
│   └── terraform/              # (future)
├── docs/
│   ├── 01_Reverse_Engineering_Report.md
│   ├── 02_PRD.md               # (this document)
│   ├── 03_SRS.md
│   ├── 04_UI_Specification.md
│   ├── 05_Database_Design.md
│   └── 06_API_Specification.md
└── docker/
    └── piston/                 # (future, for server-side execution)
```

---

# 15. Appendix — Free-Tier Limits Reference

| Service | Limit | How We Stay Within |
|---|---|---|
| Vercel Hobby | 100GB bandwidth/mo | Optimized images, CDN caching, minimal JS |
| Neon Free | 500MB DB, 100k compute credits | Index optimization, data archive, no blobs |
| Cloudflare R2 | 10GB storage, 1M reads/mo | Only store evaluations, no raw audio |
| Resend Free | 500 emails/mo | Only transactional (verification, password reset, receipts) |
| PostHog Free | 1M events/mo | Careful event planning, no noise |
| Sentry Free | 5k errors/mo | Only capture exceptions, not warnings |
| GitHub Actions | 2000 min/mo | Turborepo caching reduces build minutes |
| Stripe | 2.9% + $0.30/transaction | Standard processing fee |

---

**Revision History**

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-07-12 | Initial scaffold |
| 1.0 | 2026-07-12 | Full PRD with free-tier alignment, MVP scope, constraints |
