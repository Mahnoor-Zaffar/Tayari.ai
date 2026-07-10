import { describe, it, expect } from 'vitest';
import { detectFillerWords } from './filler-words';

describe('detectFillerWords', () => {
  it('returns empty object for clean speech', () => {
    expect(detectFillerWords('I have five years of experience with Python.')).toEqual({});
  });

  it('detects a single filler word', () => {
    const result = detectFillerWords('I um have experience.');
    expect(result).toEqual({ um: 1 });
  });

  it('counts multiple occurrences of the same filler', () => {
    const result = detectFillerWords('um, I think um, maybe um.');
    expect(result.um).toBe(3);
  });

  it('detects multiple filler types', () => {
    const result = detectFillerWords('um, like, basically, you know.');
    expect(result.um).toBe(1);
    expect(result.like).toBe(1);
    expect(result.basically).toBe(1);
    expect(result['you know']).toBe(1);
  });

  it('handles case-insensitive matching', () => {
    const result = detectFillerWords('UM Uh Like');
    expect(result.um).toBe(1);
    expect(result.uh).toBe(1);
    expect(result.like).toBe(1);
  });

  it('detects Urdu filler yaani', () => {
    const result = detectFillerWords('main ne yaani kaam kiya');
    expect(result.yaani).toBe(1);
  });

  it('handles empty string', () => {
    expect(detectFillerWords('')).toEqual({});
  });

  it('detects multi-word filler phrases', () => {
    const result = detectFillerWords('like you know, I mean');
    expect(result['like you know']).toBe(1);
    expect(result['i mean']).toBe(1);
  });
});
