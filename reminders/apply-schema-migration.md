# Action Required — Apply Schema Migration

The `match_resume_chunks` PostgreSQL function was updated to accept a
`query_user_id` parameter so RAG search only returns the current user's
resume chunks instead of leaking data between users.

**Run this in Supabase SQL Editor** (or via your migration tool):

```sql
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
```

The full updated schema is in `docs/SCHEMA.sql` for reference.
