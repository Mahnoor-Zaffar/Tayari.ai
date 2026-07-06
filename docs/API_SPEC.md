# Tayari.ai API Interface Specification

## 1. Main Turn Audio Ingestion Endpoint
- **URL:** `/api/interview/turn`
- **Method:** `POST`
- **Headers:** `Content-Type: multipart/form-data`

### Payload Parameters
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `audio` | `Blob / File` | Raw audio binary track encoded from client (`audio/webm;codecs=opus`) |
| `sessionId` | `String (UUID)` | Associated session from `interview_sessions` |
| `userId` | `String (UUID)` | Authenticated user primary key reference |

### Response Protocol (Server-Sent Events Stream)
Returns a real-time data connection chunked stream format (`text/event-stream`).

```text
DATA:TRANSCRIPT:{"text": "So basically I scaled the PostgreSQL database using read-replicas."}

DATA:CHUNK:{"text": "That "}
DATA:CHUNK:{"text": "sounds "}
DATA:CHUNK:{"text": "like "}
DATA:CHUNK:{"text": "a "}
DATA:CHUNK:{"text": "high-level "}
DATA:CHUNK:{"text": "solution. "}
DATA:CHUNK:{"text": "How "}
DATA:CHUNK:{"text": "did "}
DATA:CHUNK:{"text": "you "}
DATA:CHUNK:{"text": "handle "}
DATA:CHUNK:{"text": "replication "}
DATA:CHUNK:{"text": "lag?"}

2. Asynchronous Async Post-Processing Worker Webhook
URL: /api/workers/evaluate-turn

Method: POST

Access: Internal Core / Signed Token Authorized

Body Payload
JSON
{
  "turnId": "3b2f518e-9988-4444-a1a1-33c33b3b3b3b",
  "interviewer_question": "How did you scale the system data engine layer?",
  "candidate_response": "So basically I scaled the PostgreSQL database using read-replicas, um, you know, because traffic was heavy."
}
Execution Steps
Parse candidate_response for native local filler words (um, like, yaani, basically, you know).

Forward payloads to the Shadow Evaluator LLM API.

Update table turn_evaluations matching turn_id === turnId.


---

## 3. Database Schema & Migration Script (`SCHEMA.sql`)

```sql
-- ============================================================================
-- TAYARI.AI CORE DATABASE INITIALIZATION SCHEMA
-- Target Engine: PostgreSQL (Supabase Default Environment)
-- ============================================================================

-- Step 1: Enable the Vector extension module
create extension if not exists vector;

-- Step 2: Global Configuration Session Table
create table public.interview_sessions (
    id uuid default gen_random_uuid() primary key,
    user_id uuid not null,
    target_role text not null,
    difficulty text not null check (difficulty in ('Junior', 'Mid', 'Senior', 'Staff')),
    current_stage text not null default 'INTRO' check (current_stage in ('INTRO', 'TECHNICAL', 'BEHAVIORAL', 'WRAP_UP')),
    resume_context text,
    is_completed boolean not null default false,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Step 3: Conversation History Registry Ledger
create table public.interview_turns (
    id uuid default gen_random_uuid() primary key,
    session_id uuid references public.interview_sessions(id) on delete cascade not null,
    sequence_number integer not null,
    interviewer_question text not null,
    candidate_response text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique (session_id, sequence_number)
);

-- Step 4: Analytical Scorecard Feedback Matrix
create table public.turn_evaluations (
    id uuid default gen_random_uuid() primary key,
    turn_id uuid references public.interview_turns(id) on delete cascade not null unique,
    technical_score integer check (technical_score >= 1 and technical_score <= 10),
    communication_score integer check (communication_score >= 1 and communication_score <= 10),
    star_framework_check boolean default false not null,
    constructive_critique text,
    filler_words_detected jsonb default '{}'::jsonb not null
);

-- Step 5: Resume Vector Embeddings Registry
create table public.resume_embeddings (
    id bigint generated always as identity primary key,
    user_id uuid not null,
    content text not null,
    embedding vector(1536) not null,
    metadata jsonb default '{}'::jsonb
);

-- Step 6: Create Indexes for Performance Optimization (Sub-50ms query speeds)
create index idx_turns_session on public.interview_turns(session_id, sequence_number);
create index idx_evaluations_turn on public.turn_evaluations(turn_id);