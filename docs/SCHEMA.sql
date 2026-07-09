-- ============================================================================
-- Tayari.ai — Database Foundation Migration
-- Version: 1.0.0
-- Target: Supabase (PostgreSQL 15+ / pgvector 0.5+)
-- ============================================================================

-- 1. Enable pgvector extension for semantic search over resume embeddings
create extension if not exists vector
with schema public;

-- ============================================================================
-- 2. interview_sessions — Global session configuration tracker
-- ============================================================================
create table public.interview_sessions (
    id          uuid default gen_random_uuid() primary key,
    user_id     uuid not null,
    target_role text not null,
    difficulty  text not null check (difficulty in ('Junior', 'Mid', 'Senior', 'Staff')),
    current_stage text not null default 'INTRO' check (current_stage in ('INTRO', 'TECHNICAL', 'BEHAVIORAL', 'WRAP_UP')),
    resume_context text,
    is_completed boolean not null default false,
    created_at  timestamp with time zone default timezone('utc'::text, now()) not null
);

-- ============================================================================
-- 3. interview_turns — Chronological conversation turn ledger
-- ============================================================================
create table public.interview_turns (
    id                  uuid default gen_random_uuid() primary key,
    session_id          uuid references public.interview_sessions(id) on delete cascade not null,
    sequence_number     integer not null,
    interviewer_question text not null,
    candidate_response  text not null,
    created_at          timestamp with time zone default timezone('utc'::text, now()) not null,

    unique (session_id, sequence_number)
);

-- ============================================================================
-- 4. turn_evaluations — Shadow evaluator scorecard matrix
-- ============================================================================
create table public.turn_evaluations (
    id                   uuid default gen_random_uuid() primary key,
    turn_id              uuid references public.interview_turns(id) on delete cascade not null unique,
    technical_score      integer check (technical_score >= 1 and technical_score <= 10),
    communication_score  integer check (communication_score >= 1 and communication_score <= 10),
    star_framework_check boolean not null default false,
    constructive_critique text,
    filler_words_detected jsonb not null default '{}'::jsonb,
    created_at           timestamp with time zone default timezone('utc'::text, now()) not null
);

-- ============================================================================
-- 5. resume_embeddings — Candidate resume chunk vector store
-- ============================================================================
create table public.resume_embeddings (
    id        bigint generated always as identity primary key,
    user_id   uuid not null,
    content   text not null,
    embedding vector(384) not null,
    metadata  jsonb default '{}'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- ============================================================================
-- 6. match_resume_chunks — Cosine similarity search function
-- ============================================================================
create or replace function public.match_resume_chunks(
    query_embedding vector(384),
    query_user_id uuid,
    match_threshold float,
    match_count int
)
returns table (
    id         bigint,
    user_id    uuid,
    content    text,
    metadata   jsonb,
    similarity float
)
language plpgsql
stable
as $$
begin
    return query
    select
        re.id,
        re.user_id,
        re.content,
        re.metadata,
        1 - (re.embedding <=> query_embedding) as similarity
    from public.resume_embeddings re
    where re.user_id = query_user_id
      and 1 - (re.embedding <=> query_embedding) > match_threshold
    order by re.embedding <=> query_embedding
    limit match_count;
end;
$$;

-- ============================================================================
-- 7. B-tree indexes for sub-50ms foreign-key lookups
-- ============================================================================
create index if not exists idx_interview_sessions_user_id
    on public.interview_sessions(user_id);

create index if not exists idx_interview_turns_session_id
    on public.interview_turns(session_id, sequence_number);

create index if not exists idx_turn_evaluations_turn_id
    on public.turn_evaluations(turn_id);

create index if not exists idx_resume_embeddings_user_id
    on public.resume_embeddings(user_id);

-- ============================================================================
-- 8. v1.1 migration — Enhanced evaluation dimensions
-- ============================================================================
alter table public.turn_evaluations
    add column if not exists conciseness_score integer check (conciseness_score >= 1 and conciseness_score <= 5),
    add column if not exists confidence_score  integer check (confidence_score >= 1 and confidence_score <= 5),
    add column if not exists code_quality_score integer check (code_quality_score >= 1 and code_quality_score <= 5);

alter table public.interview_sessions
    add column if not exists overall_assessment text;
