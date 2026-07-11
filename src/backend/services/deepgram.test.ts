import { describe, it, expect } from 'vitest';
import { extractTranscript } from './deepgram';

describe('extractTranscript', () => {
  it('extracts transcript from a valid response', () => {
    const response = {
      results: {
        channels: [
          {
            alternatives: [{ transcript: 'hello world' }],
          },
        ],
      },
    };
    expect(extractTranscript(response)).toBe('hello world');
  });

  it('returns empty string when no results', () => {
    expect(extractTranscript({})).toBe('');
  });

  it('returns empty string when channels is empty', () => {
    const response = {
      results: { channels: [] },
    };
    expect(extractTranscript(response)).toBe('');
  });

  it('returns empty string when alternatives is empty', () => {
    const response = {
      results: {
        channels: [{ alternatives: [] }],
      },
    };
    expect(extractTranscript(response)).toBe('');
  });

  it('returns empty string when transcript is missing', () => {
    const response: Record<string, unknown> = {
      results: {
        channels: [{ alternatives: [{}] }],
      },
    };
    expect(extractTranscript(response as never)).toBe('');
  });

  it('returns empty string when channels is undefined', () => {
    const response = {
      results: {},
    };
    expect(extractTranscript(response)).toBe('');
  });

  it('handles deeply nested null/undefined gracefully', () => {
    const response: Record<string, unknown> = {
      results: {
        channels: [null],
      },
    };
    expect(extractTranscript(response as never)).toBe('');
  });
});

describe('transcribeAudioBuffer input validation', () => {
  it('throws on audio smaller than 1024 bytes', async () => {
    const { transcribeAudioBuffer } = await import('./deepgram');
    const small = Buffer.alloc(512);
    await expect(transcribeAudioBuffer(small, 'audio/webm')).rejects.toThrow(
      'Audio too small',
    );
  });
});
