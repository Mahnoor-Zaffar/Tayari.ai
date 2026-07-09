import OpenAI from 'openai';
import type { Stream } from 'openai/streaming';
import type { ShadowEvaluatorContract } from '@/types/interview';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
  baseURL: process.env.OPENAI_BASE_URL || 'https://openrouter.ai/api/v1',
  ...(process.env.OPENAI_BASE_URL
    ? {}
    : {
        defaultHeaders: {
          'HTTP-Referer': 'https://tayari.ai',
          'X-Title': 'Tayari.ai',
        },
      }),
});

export async function streamChat(
  messages: OpenAI.Chat.ChatCompletionMessageParam[],
): Promise<Stream<OpenAI.Chat.Completions.ChatCompletionChunk>> {
  return openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages,
    stream: true,
    temperature: 0.7,
    max_tokens: 256,
  });
}

const EVALUATION_SYSTEM_PROMPT = `You are an expert executive interview coach. Your task is to critique the candidate's last answer with extreme candor.

Processing Directives:
1. Grade the technical depth based on specific architectures, trade-offs, and metrics mentioned (1-10).
2. Grade the communication structure — logical flow, clarity, STAR compliance for behavioral answers (1-10).
3. Did they use the STAR framework (Situation, Task, Action, Result) for behavioral answers? (boolean)
4. Grade conciseness — did they answer directly vs. circle around or ramble? (1-5)
5. Grade confidence based on hedging language, definitive assertions vs. tentative phrasing (1-5).
6. Grade code quality / design quality — best practices, edge cases, readability (1-5, default 3 if not applicable).
7. Provide an unvarnished, direct 2-3 sentence critique: what they did well and what specific detail or structure they left out.

Your response must be a single, valid JSON object matching this schema:
{
  "technicalScore": 7,
  "communicationScore": 6,
  "starFrameworkCheck": true,
  "concisenessScore": 4,
  "confidenceScore": 3,
  "codeQualityScore": 3,
  "constructiveCritique": "Your answer named the database choice but completely failed to detail the actual sharding architecture or the read/write metrics. You also spent too long on background context before reaching the core point."
}

Do not wrap the JSON in markdown code fences. Output ONLY the JSON object.`;

export async function evaluateResponse(params: {
  interviewerQuestion: string;
  candidateResponse: string;
}): Promise<ShadowEvaluatorContract> {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'system', content: EVALUATION_SYSTEM_PROMPT },
      {
        role: 'user',
        content: `Question: ${params.interviewerQuestion}\n\nAnswer: ${params.candidateResponse}`,
      },
    ],
    response_format: { type: 'json_object' },
    temperature: 0.3,
    max_tokens: 256,
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

  const required = {
    technicalScore: 'number',
    communicationScore: 'number',
    starFrameworkCheck: 'boolean',
    concisenessScore: 'number',
    confidenceScore: 'number',
    codeQualityScore: 'number',
    constructiveCritique: 'string',
  } as const;

  for (const [key, type] of Object.entries(required)) {
    if (typeof parsed[key] !== type) {
      throw new Error(`Evaluation LLM returned malformed JSON: "${key}" must be ${type}`);
    }
  }

  return parsed as unknown as ShadowEvaluatorContract;
}
