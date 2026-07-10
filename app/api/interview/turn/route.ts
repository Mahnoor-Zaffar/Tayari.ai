// =============================================================================
// Tayari.ai — Turn Ingestion & Streaming Response Endpoint
// -----------------------------------------------------------------------------
// POST /api/interview/turn
// Content-Type: multipart/form-data
//
// Pipeline:
//   1. Rate limit check (per-IP)
//   2. Parse audio blob + metadata from the multipart payload
//   3. Transcribe audio via Deepgram Nova-2
//   4. Embed transcript via text-embedding-3-small
//   5. RAG search over resume vectors via match_resume_chunks
//   6. Fetch session config & chronological turn history
//   7. Build the persona system prompt with RAG anchors
//   8. Stream gpt-4o-mini response as SSE events
//   9. Persist the completed turn on stream end & fire evaluation
// =============================================================================

import { NextRequest } from 'next/server';
import { createSupabaseServerClient } from '@/lib/supabase/server';
import { transcribeAudio } from '@/backend/services/deepgram';
import type { TranscribeOptions } from '@/backend/services/deepgram';
import { streamChat, evaluateResponse } from '@/backend/services/openai';
import { generateEmbedding } from '@/backend/services/embeddings';
import {
  fetchSession,
  fetchTurnHistory,
  insertTurn,
  upsertEvaluation,
  searchResumeContext,
  completeSession,
  updateSessionStage,
} from '@/backend/db/database';
import { detectFillerWords } from '@/backend/services/filler-words';
import { buildInterviewerPrompt } from '@/backend/services/prompts';
import { encodeSSE } from '@/backend/services/utils';
import type { SSEEvent, InterviewStage } from '@/types/interview';
import { stageForTurnNumber, MAX_TURNS } from '@/types/interview';
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions';
import { checkRateLimit } from '@/lib/rate-limit';

// ---------------------------------------------------------------------------
// Keyword boost list — injected into Deepgram to improve recognition of
// technical terms and localised Urdu/English filler tokens common in
// Pakistani tech interviews.
// ---------------------------------------------------------------------------
const TECH_KEYWORDS: TranscribeOptions = {
  keywords: [
    'Next.js', 'Supabase', 'pgvector', 'Zustand', 'PostgreSQL',
    'TypeScript', 'JavaScript', 'React', 'Node.js', 'Docker',
    'Kubernetes', 'AWS', 'Vercel', 'Prisma', 'Tailwind',
    'yaani', 'matlab', 'acha', 'hai', 'falan',
    'pandas', 'numpy', 'FastAPI', 'GraphQL', 'Redis',
    'CI/CD', 'microservices', 'monorepo', 'WebSocket', 'REST',
  ],
};

export async function POST(req: NextRequest) {
  // -------------------------------------------------------------------------
  // 1. Rate limit
  // -------------------------------------------------------------------------

  const ip = req.headers.get('x-forwarded-for') ?? 'unknown';
  const { allowed, retryAfter } = checkRateLimit(`turn:${ip}`);
  if (!allowed) {
    return new Response(JSON.stringify({ error: 'Too many requests' }), {
      status: 429,
      headers: { 'Retry-After': String(retryAfter) },
    });
  }

  // -------------------------------------------------------------------------
  // 2. Parse multipart form data
  // -------------------------------------------------------------------------

  let audioBlob: Blob | null = null;
  let sessionId: string;
  let isSkip = false;
  let isEnd = false;

  try {
    const form = await req.formData();
    const skip = form.get('skip');
    const end = form.get('end');
    const sid = form.get('sessionId');

    if (end === 'true') {
      isEnd = true;
    } else if (skip === 'true') {
      isSkip = true;
    } else {
      const file = form.get('audio');
      if (!(file instanceof Blob)) {
        return new Response('Missing or invalid "audio" field', { status: 400 });
      }
      audioBlob = file;
    }

    if (typeof sid !== 'string' || !sid) {
      return new Response('Missing or invalid "sessionId" field', { status: 400 });
    }

    sessionId = sid;
  } catch (err) {
    console.error('[turn] Form parse error:', err instanceof Error ? err.message : err);
    return new Response('Failed to parse request body', { status: 400 });
  }

  // -------------------------------------------------------------------------
  // 2. Authenticate user (required for user-scoped RAG)
  // -------------------------------------------------------------------------

  let userId: string;

  try {
    const supabase = await createSupabaseServerClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return new Response('Unauthorised', { status: 401 });
    }

    userId = user.id;
  } catch (err) {
    console.error('[turn] Auth error:', err instanceof Error ? err.message : err);
    return new Response('Authentication failed', { status: 500 });
  }

  // -------------------------------------------------------------------------
  // 3. Transcribe audio → text  (Deepgram Nova-2-Phonecall)
  //    If skip flag is set, use a placeholder transcript instead.
  // -------------------------------------------------------------------------

  let transcript: string;

  if (isEnd) {
    transcript = "I'd like to end the interview here and get my final feedback.";
  } else if (isSkip) {
    transcript = "I'd like to skip this question and move on to the next one.";
  } else {
    try {
      transcript = await transcribeAudio(audioBlob!, TECH_KEYWORDS);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Transcription failed';
      console.error('[turn] Transcription error:', message);

      const errorStream = new ReadableStream({
        start(controller) {
          controller.enqueue(encodeSSE({ type: 'ERROR', data: { message } }));
          controller.close();
        },
      });

      return new Response(errorStream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
        },
      });
    }
  }

  // -------------------------------------------------------------------------
  // 4. Fetch session details & historical conversation
  // 5. Embed transcript & RAG (only for real audio — skip for skip/end)
  // -------------------------------------------------------------------------

  let session: Awaited<ReturnType<typeof fetchSession>>;
  let turnHistory: Awaited<ReturnType<typeof fetchTurnHistory>>;

  try {
    [session, turnHistory] = await Promise.all([
      fetchSession(sessionId),
      fetchTurnHistory(sessionId),
    ]);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Pre-stream pipeline failed';
    console.error('[turn] Pre-stream error:', message);
    return new Response(message, { status: 500 });
  }

  // Guard: reject turns on already-completed sessions
  if (session.isCompleted) {
    return new Response('This interview session is already completed. Please start a new interview.', { status: 400 });
  }

  let ragChunks: Awaited<ReturnType<typeof searchResumeContext>> = [];

  if (!isSkip && !isEnd) {
    try {
      const embedding = await generateEmbedding(transcript);
      ragChunks = await searchResumeContext(embedding, userId, 0.7, 5);
    } catch (err) {
      console.error('[turn] Embedding/RAG error:', err instanceof Error ? err.message : err);
      // Non-fatal — proceed without RAG context
    }
  }

  // -------------------------------------------------------------------------
  // 7. Stage progression — determine current stage from turn number
  // -------------------------------------------------------------------------

  const thisTurnNumber = turnHistory.length + 1;
  const stage: InterviewStage = isEnd || thisTurnNumber > MAX_TURNS
    ? 'WRAP_UP'
    : stageForTurnNumber(thisTurnNumber);

  if (stage !== session.currentStage) {
    await updateSessionStage(sessionId, stage).catch((err) =>
      console.error('[turn] Failed to update stage:', err),
    );
  }

  // -------------------------------------------------------------------------
  // 8. Build system prompt with RAG anchors
  // -------------------------------------------------------------------------

  const systemPrompt = buildInterviewerPrompt({
    targetRole: session.targetRole,
    difficulty: session.difficulty,
    currentStage: stage,
  });

  // -------------------------------------------------------------------------
  // 9. Build message list & initiate OpenAI streaming
  // -------------------------------------------------------------------------

  const ragContextMessage = ragChunks.length > 0
    ? `Relevant context from the candidate's resume (use this to tailor your next question):\n${ragChunks.map((c) => c.content).join('\n---\n')}`
    : null;

  const messages: ChatCompletionMessageParam[] = [
    { role: 'system', content: systemPrompt },
    ...turnHistory.flatMap((t) => [
      { role: 'assistant' as const, content: t.interviewerQuestion },
      { role: 'user' as const, content: t.candidateResponse },
    ]),
    ...(ragContextMessage ? [{ role: 'system' as const, content: ragContextMessage }] : []),
    { role: 'user', content: transcript },
  ];

  let openaiStream: Awaited<ReturnType<typeof streamChat>>;

  try {
    openaiStream = await streamChat(messages);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Failed to start LLM stream';
    console.error('[turn] LLM stream error:', message);
    return new Response(message, { status: 500 });
  }

  // -------------------------------------------------------------------------
  // 9. Return SSE ReadableStream
  // -------------------------------------------------------------------------

  const isCompleted = stage === 'WRAP_UP';

  const stream = new ReadableStream({
    async start(controller) {
      const enqueue = (event: SSEEvent) => controller.enqueue(encodeSSE(event));

      try {
        enqueue({ type: 'TRANSCRIPT', data: { text: transcript } });

        let fullResponse = '';

        for await (const chunk of openaiStream) {
          const token = chunk.choices?.[0]?.delta?.content;
          if (token) {
            fullResponse += token;
            enqueue({ type: 'CHUNK', data: { text: token } });
          }
        }

        const nextSequenceNumber = turnHistory.length + 1;

        const turnId = await insertTurn({
          sessionId,
          sequenceNumber: nextSequenceNumber,
          interviewerQuestion: fullResponse,
          candidateResponse: transcript,
        });

        // Background evaluation (fire-and-forget — never blocks the SSE stream)
        const fillerWordsDetected = detectFillerWords(transcript);
        evaluateResponse({
          interviewerQuestion: fullResponse,
          candidateResponse: transcript,
        })
          .then((evaluation) =>
            upsertEvaluation({
              turnId,
              technicalScore: evaluation.technicalScore,
              communicationScore: evaluation.communicationScore,
              starFrameworkCheck: evaluation.starFrameworkCheck,
              concisenessScore: evaluation.concisenessScore,
              confidenceScore: evaluation.confidenceScore,
              codeQualityScore: evaluation.codeQualityScore,
              constructiveCritique: evaluation.constructiveCritique,
              fillerWordsDetected,
            }),
          )
          .catch((err) => {
            console.error('[turn] Background evaluation failed:', err.message);
          });

        // Mark session complete if WRAP_UP
        if (isCompleted) {
          completeSession(sessionId, fullResponse).catch((err) =>
            console.error('[turn] Failed to complete session:', err),
          );
        }

        enqueue({
          type: 'DONE',
          data: {
            turnId,
            interviewerQuestion: fullResponse,
            candidateResponse: transcript,
            completed: isCompleted,
          },
        });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Stream error';
        enqueue({ type: 'ERROR', data: { message } });
      } finally {
        controller.close();
      }
    },

    cancel() {
      return;
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
