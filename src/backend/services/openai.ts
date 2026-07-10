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
    model: 'gpt-4o',
    messages,
    stream: true,
    temperature: 0.7,
    max_tokens: 512,
  });
}

const EVALUATION_SYSTEM_PROMPT = `You are a balanced senior interview coach providing constructive feedback.

Score anchors:
- 1-10 scales (technicalScore, communicationScore): 1-2=poor, 3-4=below avg, 5-6=average, 7-8=good, 9-10=excellent
- 1-5 scales (concisenessScore, confidenceScore, codeQualityScore): 1=poor, 2=below avg, 3=average, 4=good, 5=excellent

Processing Directives:
1. technicalScore (1-10): Rate the technical depth — specific architectures, trade-offs, metrics, and tools mentioned.
2. communicationScore (1-10): Rate the logical flow, clarity, and STAR compliance for behavioral answers.
3. starFrameworkCheck (boolean): Did they use Situation, Task, Action, Result for a behavioral question?
4. concisenessScore (1-5): Did they answer directly vs. ramble or repeat themselves?
5. confidenceScore (1-5): Rate based on hedging language ("I think", "maybe") vs. definitive assertions.
6. codeQualityScore (1-5): Code/design quality — best practices, edge cases, readability. Default 3 if not applicable.
7. constructiveCritique: A balanced 2-3 sentence critique: start with what they did well, then 1 specific area to improve.

Use the full range of each scale — don't cluster scores in the middle. An exceptional answer should get 9-10; a poor one should get 1-2.

Your response must be a single, valid JSON object matching this schema:
{
  "technicalScore": 7,
  "communicationScore": 6,
  "starFrameworkCheck": true,
  "concisenessScore": 4,
  "confidenceScore": 3,
  "codeQualityScore": 3,
  "constructiveCritique": "You gave a solid overview of the architecture including the sharding strategy, but you didn't mention the actual read/write throughput metrics you observed. Next time, lead with the numbers."
}

Do not wrap the JSON in markdown code fences. Output ONLY the JSON object.`;

export async function evaluateResponse(params: {
  interviewerQuestion: string;
  candidateResponse: string;
}): Promise<ShadowEvaluatorContract> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  const response = await openai.chat.completions.create(
    {
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: EVALUATION_SYSTEM_PROMPT },
        {
          role: 'user',
          content: `Question: ${params.interviewerQuestion}\n\nAnswer: ${params.candidateResponse}`,
        },
      ],
      temperature: 0.3,
      max_tokens: 512,
    },
    { signal: controller.signal },
  );

  clearTimeout(timeout);

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
