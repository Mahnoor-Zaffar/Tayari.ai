// =============================================================================
// Tayari.ai — Shared Utilities
// =============================================================================

import type { SSEEvent } from '@/types/interview';

const TEXT_ENCODER = new TextEncoder();

export function encodeSSE(event: SSEEvent): Uint8Array {
  const { type, data } = event;
  const payload = `DATA:${type}:${JSON.stringify(data)}\n\n`;
  return TEXT_ENCODER.encode(payload);
}

export function mapRowToCamel<T>(row: Record<string, unknown>): T {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(row)) {
    const camelKey = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
    result[camelKey] = value;
  }
  return result as T;
}

export function mapRowsToCamel<T>(rows: Record<string, unknown>[]): T[] {
  return rows.map((row) => mapRowToCamel<T>(row));
}
