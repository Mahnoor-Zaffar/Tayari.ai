import { z } from 'zod';

const envSchema = z.object({
  DEEPGRAM_API_KEY: z.string().min(1, 'DEEPGRAM_API_KEY is required'),
  OPENAI_API_KEY: z.string().min(1, 'OPENAI_API_KEY is required'),
  NEXT_PUBLIC_SUPABASE_URL: z.string().url('NEXT_PUBLIC_SUPABASE_URL must be a valid URL'),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1, 'NEXT_PUBLIC_SUPABASE_ANON_KEY is required'),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1, 'SUPABASE_SERVICE_ROLE_KEY is required'),
  WORKER_AUTH_TOKEN: z.string().optional(),
  OPENAI_BASE_URL: z.string().url().optional(),
});

export type Env = z.infer<typeof envSchema>;

let _parsed: Env | null = null;

export function getEnv(): Env {
  if (_parsed) return _parsed;

  const result = envSchema.safeParse(process.env);

  if (!result.success) {
    const missing = result.error.issues
      .map((i) => i.path.join('.'))
      .join(', ');
    throw new Error(`Environment validation failed: missing or invalid ${missing}`);
  }

  _parsed = result.data;
  return _parsed;
}
