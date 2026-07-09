// =============================================================================
// Tayari.ai — Turn Ingestion & Streaming Response Endpoint
// -----------------------------------------------------------------------------
// POST /api/interview/turn
// Content-Type: multipart/form-data
//
// Pipeline:
//   1. Parse audio blob + metadata from the multipart payload
//   2. Transcribe audio via Deepgram Nova-2
//   3. Embed transcript via text-embedding-3-small
//   4. RAG search over resume vectors via match_resume_chunks
//   5. Fetch session config & chronological turn history
//   6. Build the persona system prompt with RAG anchors
//   7. Stream gpt-4o-mini response as SSE events
//   8. Persist the completed turn on stream end
// =============================================================================

import { NextRequest } from 'next/server';
import { createSupabaseServerClient } from '@/lib/supabase/server';
import { transcribeAudio } from '@/backend/services/deepgram';
import { streamChat, evaluateResponse } from '@/backend/services/openai';
import { generateEmbedding } from '@/backend/services/embeddings';
import {
  fetchSession,
  fetchTurnHistory,
  insertTurn,
  upsertEvaluation,
  searchResumeContext,
} from '@/backend/db/database';
import { detectFillerWords } from '@/backend/services/filler-words';
import { buildInterviewerPrompt } from '@/backend/services/prompts';
import { encodeSSE } from '@/backend/services/utils';
import type { SSEEvent } from '@/types/interview';
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions';

export async function POST(req: NextRequest) {
  // -------------------------------------------------------------------------
  // 1. Parse multipart form data
  // -------------------------------------------------------------------------

  let audioBlob: Blob;
  let sessionId: string;

  try {
    const form = await req.formData();
    const file = form.get('audio');
    const sid = form.get('sessionId');

    if (!(file instanceof Blob)) {
      return new Response('Missing or invalid "audio" field', { status: 400 });
    }
    if (typeof sid !== 'string' || !sid) {
      return new Response('Missing or invalid "sessionId" field', { status: 400 });
    }

    audioBlob = file;
    sessionId = sid;
    console.log('[turn] Blob size:', audioBlob.size, 'type:', audioBlob.type);
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
  // 3. Transcribe audio → text  (Deepgram Nova-2)
  // -------------------------------------------------------------------------

  let transcript: string;

  try {
    transcript = await transcribeAudio(audioBlob);
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

  // -------------------------------------------------------------------------
  // 4. Embed transcript  (text-embedding-3-small)
  // 5. RAG — retrieve matching resume context (scoped to current user)
  // 6. Fetch session details & historical conversation
  // -------------------------------------------------------------------------

  let embedding: number[];
  let ragChunks: Awaited<ReturnType<typeof searchResumeContext>>;
  let session: Awaited<ReturnType<typeof fetchSession>>;
  let turnHistory: Awaited<ReturnType<typeof fetchTurnHistory>>;

  try {
    [embedding, session, turnHistory] = await Promise.all([
      generateEmbedding(transcript),
      fetchSession(sessionId),
      fetchTurnHistory(sessionId),
    ]);

    ragChunks = await searchResumeContext(embedding, userId, 0.7, 5);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Pre-stream pipeline failed';
    console.error('[turn] Pre-stream error:', message);
    return new Response(message, { status: 500 });
  }

  // -------------------------------------------------------------------------
  // 7. Build system prompt with RAG anchors
  // -------------------------------------------------------------------------

  const contextualBackground = ragChunks.map((c) => c.content).join('\n---\n');

  const systemPrompt = buildInterviewerPrompt({
    targetRole: session.targetRole,
    difficulty: session.difficulty,
    currentStage: session.currentStage,
    contextualBackground,
  });

  // -------------------------------------------------------------------------
  // 8. Build message list & initiate OpenAI streaming
  // -------------------------------------------------------------------------

  const messages: ChatCompletionMessageParam[] = [
    { role: 'system', content: systemPrompt },
    ...turnHistory.flatMap((t) => [
      { role: 'assistant' as const, content: t.interviewerQuestion },
      { role: 'user' as const, content: t.candidateResponse },
    ]),
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
              constructiveCritique: evaluation.constructiveCritique,
              fillerWordsDetected,
            }),
          )
          .catch((err) => {
            console.error('[turn] Background evaluation failed:', err);
          });

        enqueue({
          type: 'DONE',
          data: {
            turnId,
            interviewerQuestion: fullResponse,
            candidateResponse: transcript,
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
