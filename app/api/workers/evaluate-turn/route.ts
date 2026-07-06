// =============================================================================
// Tayari.ai — Post-Turn Evaluation Worker
// -----------------------------------------------------------------------------
// POST /api/workers/evaluate-turn
// Access: Internal (signed-token authorised webhook)
//
// Runs asynchronously, outside the main conversational SSE stream, so any
// failure here must never block or delay the user-facing voice loop.
//
// Pipeline:
//   1. Accept turnId + question + candidate response
//   2. Extract filler-word frequency from the candidate response
//   3. Send QA pair to gpt-4o for structured evaluation (JSON mode)
//   4. Upsert the evaluation row into turn_evaluations
// =============================================================================

import { NextRequest, NextResponse } from 'next/server';
import { evaluateResponse } from '@/backend/services/openai';
import { upsertEvaluation } from '@/backend/db/database';
import { detectFillerWords } from '@/backend/services/filler-words';
import type { EvaluateTurnWebhookPayload } from '@/types/interview';

export async function POST(req: NextRequest) {
  // -------------------------------------------------------------------------
  // 1. Validate authorisation (internal-only)
  // -------------------------------------------------------------------------

  const authHeader = req.headers.get('authorization');
  const expectedToken = process.env.WORKER_AUTH_TOKEN;

  if (expectedToken && authHeader !== `Bearer ${expectedToken}`) {
    console.error('[evaluate-turn] Unauthorised webhook call rejected');
    return NextResponse.json({ error: 'Unauthorised' }, { status: 401 });
  }

  // -------------------------------------------------------------------------
  // 2. Parse & validate payload
  // -------------------------------------------------------------------------

  let body: EvaluateTurnWebhookPayload;

  try {
    body = await req.json();
  } catch {
    console.error('[evaluate-turn] Failed to parse request body');
    return NextResponse.json(
      { error: 'Invalid JSON body' },
      { status: 400 },
    );
  }

  const { turnId, interviewerQuestion, candidateResponse } = body;

  if (!turnId || !interviewerQuestion || !candidateResponse) {
    console.error('[evaluate-turn] Missing required fields', {
      hasTurnId: !!turnId,
      hasQuestion: !!interviewerQuestion,
      hasResponse: !!candidateResponse,
    });
    return NextResponse.json(
      { error: 'Missing required fields: turnId, interviewerQuestion, candidateResponse' },
      { status: 400 },
    );
  }

  // -------------------------------------------------------------------------
  // 3. Extract filler-word frequencies (purely local — no external call)
  // -------------------------------------------------------------------------

  let fillerWordsDetected: Record<string, number>;

  try {
    fillerWordsDetected = detectFillerWords(candidateResponse);
    console.log(
      `[evaluate-turn] Filler words detected for turn ${turnId}:`,
      fillerWordsDetected,
    );
  } catch (err) {
    // Filler detection is local & should never throw; but guard anyway.
    fillerWordsDetected = {};
    console.error('[evaluate-turn] Filler word detection failed', { error: err });
  }

  // -------------------------------------------------------------------------
  // 4. Evaluate via gpt-4o (structured JSON)
  // -------------------------------------------------------------------------

  let evaluation: Awaited<ReturnType<typeof evaluateResponse>>;

  try {
    evaluation = await evaluateResponse({
      interviewerQuestion,
      candidateResponse,
    });
    console.log(
      `[evaluate-turn] Evaluation received for turn ${turnId}:`,
      {
        technicalScore: evaluation.technicalScore,
        communicationScore: evaluation.communicationScore,
      },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    console.error('[evaluate-turn] LLM evaluation failed', { error: message, turnId });
    return NextResponse.json(
      { error: 'Evaluation LLM call failed', detail: message },
      { status: 500 },
    );
  }

  // -------------------------------------------------------------------------
  // 5. Persist evaluation to turn_evaluations
  // -------------------------------------------------------------------------

  try {
    await upsertEvaluation({
      turnId,
      technicalScore: evaluation.technicalScore,
      communicationScore: evaluation.communicationScore,
      starFrameworkCheck: evaluation.starFrameworkCheck,
      constructiveCritique: evaluation.constructiveCritique,
      fillerWordsDetected,
    });

    console.log(`[evaluate-turn] Evaluation persisted for turn ${turnId}`);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    console.error('[evaluate-turn] Database upsert failed', { error: message, turnId });
    return NextResponse.json(
      { error: 'Failed to persist evaluation', detail: message },
      { status: 500 },
    );
  }

  // -------------------------------------------------------------------------
  // 6. Acknowledge
  // -------------------------------------------------------------------------

  return NextResponse.json({
    success: true,
    turnId,
    scores: {
      technical: evaluation.technicalScore,
      communication: evaluation.communicationScore,
    },
  });
}
