// =============================================================================
// Tayari.ai — Filler Word Detection
// -----------------------------------------------------------------------------
// Scans a transcript for common Urdu/English filler words and returns a
// frequency map suitable for turn_evaluations.filler_words_detected (jsonb).
// =============================================================================

const FILLER_PATTERNS: { pattern: RegExp; label: string }[] = [
  { pattern: /\bum\b/gi, label: 'um' },
  { pattern: /\buh\b/gi, label: 'uh' },
  { pattern: /\blike\b/gi, label: 'like' },
  { pattern: /\byaani\b/gi, label: 'yaani' },
  { pattern: /\byani\b/gi, label: 'yaani' },
  { pattern: /\bbasically\b/gi, label: 'basically' },
  { pattern: /\byou know\b/gi, label: 'you know' },
  { pattern: /\bi mean\b/gi, label: 'i mean' },
  { pattern: /\blike basically\b/gi, label: 'like basically' },
  { pattern: /\bactually\b/gi, label: 'actually' },
  { pattern: /\bso basically\b/gi, label: 'so basically' },
  { pattern: /\bright\b/gi, label: 'right' },
  { pattern: /\bokay\b/gi, label: 'okay' },
  { pattern: /\blike you know\b/gi, label: 'like you know' },
];

export function detectFillerWords(text: string): Record<string, number> {
  const counts: Record<string, number> = {};

  for (const { pattern, label } of FILLER_PATTERNS) {
    const matches = text.match(pattern);
    if (matches) {
      counts[label] = (counts[label] ?? 0) + matches.length;
    }
  }

  return counts;
}
