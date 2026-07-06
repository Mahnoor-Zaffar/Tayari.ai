// =============================================================================
// Tayari.ai — OpenAI Service (Embeddings + Chat Completions)
// Models:
//   text-embedding-3-small (RAG)
//   gpt-4o-mini            (foreground streaming)
//   gpt-4o                 (background evaluation)
// =============================================================================

import OpenAI from 'openai';
import type { Stream } from 'openai/streaming';
import type { ShadowEvaluatorContract } from '@/types/interview';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
});

export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text,
  });

  return response.data[0].embedding;
}

export async function streamChat(
  messages: OpenAI.Chat.ChatCompletionMessageParam[],
): Promise<Stream<OpenAI.Chat.Completions.ChatCompletionChunk>> {
  return openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages,
    stream: true,
    temperature: 0.7,
    max_tokens: 1024,
  });
}

const EVALUATION_SYSTEM_PROMPT = `You are an expert executive interview coach. Your task is to critique the candidate's last answer with extreme candor.

Processing Directives:
1. Grade the technical depth based on specific architectures, trade-offs, and metrics mentioned.
2. Grade the communication structure. If behavioral, verify if they clearly tracked the STAR framework (Situation, Task, Action, Result).
3. Provide an unvarnished, direct 1-2 sentence critique explaining exactly what detail they left out or how to strengthen their phrase.

Your response must be a single, valid JSON object matching this schema:
{
  "technicalScore": 7,
  "communicationScore": 6,
  "starFrameworkCheck": true,
  "constructiveCritique": "Your answer named the database choice but completely failed to detail the actual sharding architecture or the read/write metrics."
}

Do not wrap the JSON in markdown code fences. Output ONLY the JSON object.`;

export async function evaluateResponse(params: {
  interviewerQuestion: string;
  candidateResponse: string;
}): Promise<ShadowEvaluatorContract> {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: EVALUATION_SYSTEM_PROMPT },
      {
        role: 'user',
        content: `Question: ${params.interviewerQuestion}\n\nAnswer: ${params.candidateResponse}`,
      },
    ],
    response_format: { type: 'json_object' },
    temperature: 0.3,
    max_tokens: 512,
  });

  const raw = response.choices[0]?.message?.content;
  if (!raw) {
    throw new Error('Evaluation LLM returned empty response');
  }

  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error('Evaluation LLM returned unparseable JSON');
  }

  if (
    typeof parsed.technicalScore !== 'number' ||
    typeof parsed.communicationScore !== 'number' ||
    typeof parsed.starFrameworkCheck !== 'boolean' ||
    typeof parsed.constructiveCritique !== 'string'
  ) {
    throw new Error('Evaluation LLM returned malformed JSON (missing or invalid fields)');
  }

  return parsed as unknown as ShadowEvaluatorContract;
}
