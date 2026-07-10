const buckets = new Map<string, number[]>();
const WINDOW_MS = 60_000;
const MAX_REQUESTS = 20;

export function checkRateLimit(key: string): { allowed: boolean; retryAfter?: number } {
  const now = Date.now();
  const timestamps = buckets.get(key) ?? [];
  const withinWindow = timestamps.filter((t) => now - t < WINDOW_MS);

  if (withinWindow.length >= MAX_REQUESTS) {
    const oldest = withinWindow[0];
    return { allowed: false, retryAfter: Math.ceil((oldest + WINDOW_MS - now) / 1000) };
  }

  withinWindow.push(now);
  buckets.set(key, withinWindow);
  return { allowed: true };
}
