# Tayari.ai — AI-Powered Conversational Interview Coach

Tayari.ai is a voice-driven, multi-agent interview simulation platform that prepares candidates for rigorous technical and behavioral interviews. Unlike static question banks, it delivers a full-duplex conversational experience with real-time transcription, retrieval-augmented generation (RAG) grounded on the candidate's own resume, and an asynchronous shadow evaluator that scores every response.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js)                        │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐  │
│  │ Session  │  │ Stream   │  │   Mic     │  │  Zustand      │  │
│  │  Card    │  │ Console  │  │  Button   │  │  Store        │  │
│  └──────────┘  └──────────┘  └───────────┘  │ (State Mach.) │  │
│       │              ▲              │        └───────────────┘  │
│       │              │  SSE Stream  │                               │
│       ▼              │   (CHUNK)    ▼                               │
│  ┌──────────────────────────────────────────────┐                  │
│  │        fetch POST /api/interview/turn        │                  │
│  │        multipart/form-data (audio blob)      │                  │
│  └──────────────────────┬───────────────────────┘                  │
└─────────────────────────┼──────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────────┐
│           Next.js API Layer (Node.js Runtime)                     │
│                          │                                         │
│                          ▼                                         │
│  ┌──────────────────────────────────────────────┐                 │
│  │         /api/interview/turn  (POST)          │                 │
│  │                                              │                 │
│  │  1. Parse multipart form (audio + metadata)  │                 │
│  │  2. Transcribe via Deepgram Nova-2           │                 │
│  │  3. Embed transcript (text-embedding-3-small)│                 │
│  │  4. RAG search over resume vectors            │                 │
│  │  5. Fetch session + conversation history      │                 │
│  │  6. Build persona prompt with RAG anchors     │                 │
│  │  7. Stream gpt-4o-mini response              │                 │
│  │  8. Persist turn to DB on stream close       │                 │
│  └──────────────────────┬───────────────────────┘                 │
│                         │                                         │
│                         │ (background webhook)                    │
│                         ▼                                         │
│  ┌──────────────────────────────────────────────┐                 │
│  │     /api/workers/evaluate-turn  (POST)       │                 │
│  │                                              │                 │
│  │  1. Detect filler words (regex)              │                 │
│  │  2. Evaluate via gpt-4o (JSON mode)          │                 │
│  │  3. Upsert turn_evaluations row              │                 │
│  └──────────────────────┬───────────────────────┘                 │
└─────────────────────────┼──────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────────┐
│              Supabase (PostgreSQL + pgvector)                     │
│                          │                                         │
│  ┌──────────────────────────────────────────────┐                 │
│  │  interview_sessions     interview_turns      │                 │
│  │  turn_evaluations       resume_embeddings    │                 │
│  │                                              │                 │
│  │  match_resume_chunks(query_embedding, ...)   │                 │
│  │    → cosine similarity search                │                 │
│  └──────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 14+ (App Router) | Server-rendered React, file-based routing |
| **Language** | TypeScript (strict) | End-to-end type safety, zero `any` |
| **Styling** | Tailwind CSS | Utility-first, responsive design |
| **State** | Zustand | Lightweight global state machine (IDLE → RECORDING → PROCESSING → STREAMING_RESPONSE) |
| **Database** | Supabase (PostgreSQL 15) | Managed Postgres with real-time capabilities |
| **Vector Search** | pgvector | Cosine similarity over 1536-dim OpenAI embeddings |
| **STT** | Deepgram Nova-2 | Sub-300ms transcription with filler word detection |
| **Foreground AI** | GPT-4o-mini | Low-latency streaming interviewer persona |
| **Background AI** | GPT-4o | Structured JSON evaluation (JSON mode) |
| **Audio** | Web Audio API / MediaRecorder | Browser-native capture (`audio/webm;codecs=opus`) |
| **Streaming** | Server-Sent Events (SSE) | Real-time token delivery to the client |

---

## Project Structure

```
app/
├── api/
│   ├── interview/turn/route.ts        # Main turn ingestion + SSE stream
│   └── workers/evaluate-turn/route.ts # Background evaluation webhook
└── interview/[id]/page.tsx            # Interview workspace UI
components/interview/
├── SessionCard.tsx                     # Left sidebar metadata panel
├── StreamConsole.tsx                   # Terminal-style chat console
└── MicButton.tsx                       # Microphone toggle button
hooks/
└── useMediaRecorder.ts                 # MediaRecorder abstraction
stores/
└── interview-store.ts                  # Zustand state machine
lib/
├── deepgram.ts                         # Deepgram transcription client
├── openai.ts                           # OpenAI embedding + streaming + evaluation
├── database.ts                         # Supabase data access layer
├── prompts.ts                          # Interviewer persona prompt builder
├── filler-words.ts                     # Filler word frequency detector
└── utils.ts                            # SSE encoder + camelCase mapper
types/
└── interview.ts                        # Domain type definitions
database/
└── 001_initialize_schema.sql           # PostgreSQL migration (pgvector + tables + indexes)
```

---

## Setup

### Prerequisites

- Node.js 20+
- A Supabase project (PostgreSQL 15+ with pgvector enabled)
- Deepgram API key (Nova-2 model access)
- OpenAI API key (GPT-4o and text-embedding-3-small access)

### Installation

```bash
npm install
```

### Environment Variables

Create `.env.local`:

```env
# Deepgram
DEEPGRAM_API_KEY=dg_xxx

# OpenAI
OPENAI_API_KEY=sk-xxx

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxx

# Worker auth (shared secret for internal webhook calls)
WORKER_AUTH_TOKEN=tayari-worker-token-xxx
```

### Database Migration

Run the migration against your Supabase project:

```bash
# via Supabase CLI
supabase db push

# or execute manually in the Supabase SQL editor
# open database/001_initialize_schema.sql and run
```

### Development

```bash
npm run dev
```

---

## How It Works

### Turn Lifecycle

1. **IDLE** — The user sees the mic button. No active session state.
2. **RECORDING** — The user taps the mic. `getUserMedia` acquires the mic, `MediaRecorder` captures audio in `audio/webm;codecs=opus` chunks.
3. **PROCESSING** — The user taps again to stop. The audio blob is wrapped in `FormData` and `POST`ed to `/api/interview/turn`.
4. **STREAMING_RESPONSE** — The server returns an SSE stream. The client parses `DATA:TRANSCRIPT`, `DATA:CHUNK`, and `DATA:DONE` events, rendering tokens character-by-character in the terminal console.
5. **Back to IDLE** — After the turn persists, the UI resets for the next question.

### Dual-Agent Architecture

| Agent | Model | Runs | Purpose |
|---|---|---|---|
| **Interviewer** | GPT-4o-mini | Foreground, per-turn streaming | Generates the next question grounded on the candidate's resume and conversation history |
| **Shadow Evaluator** | GPT-4o | Background, async webhook | Scores technical depth (1–10), communication (1–10), STAR compliance, and writes a constructive critique. Runs independently; never blocks the voice loop. |

### RAG Pipeline

1. User speaks → Deepgram transcribes → transcript is embedded via `text-embedding-3-small`
2. The embedding is passed to `match_resume_chunks()` (pgvector cosine similarity)
3. Top-5 resume chunks are injected as RAG anchors into the interviewer's system prompt
4. The interviewer asks follow-up questions specifically targeting gaps or highlights in the candidate's actual background

---

## API Surface

### `POST /api/interview/turn` — Main Conversation Turn

- **Content-Type:** `multipart/form-data`
- **Fields:** `audio` (Blob, webm/opus), `sessionId` (UUID), `userId` (UUID)
- **Response:** `text/event-stream`

```
DATA:TRANSCRIPT:{"text":"..."}
DATA:CHUNK:{"text":"That "}
DATA:CHUNK:{"text":"sounds "}
...
DATA:DONE:null
```

### `POST /api/workers/evaluate-turn` — Background Evaluation

- **Content-Type:** `application/json`
- **Auth:** `Authorization: Bearer <WORKER_AUTH_TOKEN>`
- **Body:** `{ turnId, interviewerQuestion, candidateResponse }`
- **Response:** `{ success, turnId, scores }`

---

## Database Schema

| Table | Purpose | Key Columns |
|---|---|---|
| `interview_sessions` | Session-level config | `target_role`, `difficulty`, `current_stage`, `resume_context` |
| `interview_turns` | Chronological Q&A ledger | `session_id` (FK), `sequence_number` (unique per session), Q&A text |
| `turn_evaluations` | Per-turn analytics | `turn_id` (FK, unique), technical/communication scores, STAR flag, critique, filler word map |
| `resume_embeddings` | Resume chunk vector store | `embedding vector(1536)`, `content`, `metadata` (JSONB) |
| `match_resume_chunks()` | Cosine similarity search | Takes query vector, threshold, count → returns matching chunks ranked by similarity |

All tables use UUID primary keys, automatic `created_at` timestamps, and cascade deletes on foreign keys.

---

## Design Decisions

- **SSE over WebSockets:** Simpler infrastructure, no persistent connection manager needed. The request-response pattern maps naturally to each turn.
- **Zustand over Redux:** Minimal boilerplate, no providers, direct store subscription. The state machine fits in ~40 lines.
- **Background evaluator as separate endpoint:** Keeps the voice loop resilient. If GPT-4o evaluation fails or lags, the conversational flow is unaffected. The evaluation can be retried independently.
- **pgvector over a standalone vector DB:** Co-locates embeddings with relational data, reducing network hops and simplifying backup/restore.
- **Deepgram Nova-2 over Whisper API:** Sub-300ms transcription with native filler word detection and punctuation via `smart_format`.
