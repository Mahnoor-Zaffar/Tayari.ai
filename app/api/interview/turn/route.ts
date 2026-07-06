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
import { transcribeAudio } from '@/lib/deepgram';
import { generateEmbedding, streamChat } from '@/lib/openai';
import {
  fetchSession,
  fetchTurnHistory,
  insertTurn,
  searchResumeContext,
} from '@/lib/database';
import { buildInterviewerPrompt } from '@/lib/prompts';
import { encodeSSE } from '@/lib/utils';
import type { SSEEvent } from '@/types/interview';
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions';

export async function POST(req: NextRequest) {
  // -------------------------------------------------------------------------
  // 1. Parse multipart form data
  // -------------------------------------------------------------------------

  let audioBlob: Blob;
  let sessionId: string;
  let userId: string;

  try {
    const form = await req.formData();
    const file = form.get('audio');
    const sid = form.get('sessionId');
    const uid = form.get('userId');

    if (!(file instanceof Blob)) {
      return new Response('Missing or invalid "audio" field', { status: 400 });
    }
    if (typeof sid !== 'string' || !sid) {
      return new Response('Missing or invalid "sessionId" field', { status: 400 });
    }
    if (typeof uid !== 'string' || !uid) {
      return new Response('Missing or invalid "userId" field', { status: 400 });
    }

    audioBlob = file;
    sessionId = sid;
    userId = uid;
  } catch (err) {
    return new Response('Failed to parse request body', { status: 400 });
  }

  // -------------------------------------------------------------------------
  // 2. Transcribe audio → text  (Deepgram Nova-2)
  // -------------------------------------------------------------------------

  let transcript: string;

  try {
    transcript = await transcribeAudio(audioBlob);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Transcription failed';
    return new Response(message, { status: 500 });
  }

  // -------------------------------------------------------------------------
  // 3. Embed transcript  (text-embedding-3-small)
  // 4. RAG — retrieve matching resume context
  // 5. Fetch session details & historical conversation
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

    ragChunks = await searchResumeContext(embedding, 0.7, 5);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Pre-stream pipeline failed';
    return new Response(message, { status: 500 });
  }

  // -------------------------------------------------------------------------
  // 6. Build system prompt with RAG anchors
  // -------------------------------------------------------------------------

  const contextualBackground = ragChunks.map((c) => c.content).join('\n---\n');

  const systemPrompt = buildInterviewerPrompt({
    targetRole: session.targetRole,
    difficulty: session.difficulty,
    currentStage: session.currentStage,
    contextualBackground,
  });

  // -------------------------------------------------------------------------
  // 7. Build message list & initiate OpenAI streaming
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
    return new Response(message, { status: 500 });
  }

  // -------------------------------------------------------------------------
  // 8. Return SSE ReadableStream
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

        await insertTurn({
          sessionId,
          sequenceNumber: nextSequenceNumber,
          interviewerQuestion: fullResponse,
          candidateResponse: transcript,
        });

        enqueue({ type: 'DONE', data: null });
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
