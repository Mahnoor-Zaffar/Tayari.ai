import { describe, it, expect } from 'vitest';
import { encodeSSE, mapRowToCamel, mapRowsToCamel } from './utils';

describe('encodeSSE', () => {
  it('encodes a TRANSCRIPT event', () => {
    const event = { type: 'TRANSCRIPT' as const, data: { text: 'hello' } };
    const encoded = encodeSSE(event);
    const decoded = new TextDecoder().decode(encoded);
    expect(decoded).toBe('DATA:TRANSCRIPT:{"text":"hello"}\n\n');
  });

  it('encodes a CHUNK event', () => {
    const event = { type: 'CHUNK' as const, data: { text: 'world' } };
    const encoded = encodeSSE(event);
    const decoded = new TextDecoder().decode(encoded);
    expect(decoded).toBe('DATA:CHUNK:{"text":"world"}\n\n');
  });

  it('encodes a DONE event with turn data', () => {
    const event = {
      type: 'DONE' as const,
      data: { turnId: 'abc-123', interviewerQuestion: 'q?', candidateResponse: 'a.' },
    };
    const encoded = encodeSSE(event);
    const decoded = new TextDecoder().decode(encoded);
    expect(decoded).toContain('DATA:DONE:');
    expect(decoded).toContain('"turnId":"abc-123"');
    expect(decoded).toContain('"interviewerQuestion":"q?"');
    expect(decoded).toContain('"candidateResponse":"a."');
    expect(decoded).toContain('\n\n');
  });

  it('encodes an ERROR event', () => {
    const event = { type: 'ERROR' as const, data: { message: 'fail' } };
    const encoded = encodeSSE(event);
    const decoded = new TextDecoder().decode(encoded);
    expect(decoded).toBe('DATA:ERROR:{"message":"fail"}\n\n');
  });
});

describe('mapRowToCamel', () => {
  it('converts snake_case keys to camelCase', () => {
    const row = { user_id: '1', target_role: 'engineer', is_completed: true };
    const result = mapRowToCamel(row);
    expect(result).toEqual({ userId: '1', targetRole: 'engineer', isCompleted: true });
  });

  it('leaves already-camelCase keys unchanged', () => {
    const row = { userId: '1', targetRole: 'engineer' };
    const result = mapRowToCamel(row);
    expect(result).toEqual(row);
  });

  it('handles empty object', () => {
    expect(mapRowToCamel({})).toEqual({});
  });

  it('preserves null values', () => {
    const row = { user_id: null, target_role: 'engineer' };
    const result = mapRowToCamel(row);
    expect(result).toEqual({ userId: null, targetRole: 'engineer' });
  });
});

describe('mapRowsToCamel', () => {
  it('maps multiple rows', () => {
    const rows = [
      { user_id: '1', target_role: 'engineer' },
      { user_id: '2', target_role: 'designer' },
    ];
    const result = mapRowsToCamel(rows);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ userId: '1', targetRole: 'engineer' });
    expect(result[1]).toEqual({ userId: '2', targetRole: 'designer' });
  });

  it('handles empty array', () => {
    expect(mapRowsToCamel([])).toEqual([]);
  });
});
