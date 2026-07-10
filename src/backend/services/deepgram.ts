import { createClient } from '@deepgram/sdk';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DeepgramAlternative {
  transcript: string;
}

interface DeepgramChannel {
  alternatives: DeepgramAlternative[];
}

interface DeepgramResult {
  channels?: DeepgramChannel[];
}

interface DeepgramResponse {
  results?: DeepgramResult;
}

export interface TranscribeOptions {
  /** Domain-specific terms to boost (e.g. "Next.js", "yaani", "pgvector"). */
  keywords?: string[];
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

/**
 * Transcribe an audio blob via Deepgram.
 *
 * Accent / dialect tuning for South‑Asian English (Pakistani tech sector):
 *  - `model`: `nova-2-phonecall` — tuned for conversational speech with
 *    background noise and code‑switching (Urdu/English).
 *  - `language`: `en-IN` — tells the engine to align phonetics to South
 *    Asian English rather than North American defaults.
 *  - `keywords`: user‑supplied list injected with a moderate boost (×3)
 *    to help the model catch technical terms and localised fillers.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  options?: TranscribeOptions,
): Promise<string> {
  const arrayBuffer = await audioBlob.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);

  if (buffer.length < 1024) {
    throw new Error(`Audio too small (${buffer.length} bytes), skipping`);
  }

  // -----------------------------------------------------------------------
  // Transcription request
  // -----------------------------------------------------------------------

  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    buffer,
    {
      model: 'nova-2-phonecall',
      language: 'en-IN',
      mimetype: audioBlob.type || 'audio/webm;codecs=opus',
      smart_format: true,
      punctuate: true,
      filler_words: true,
      keywords: options?.keywords?.length
        ? options.keywords.map((k) => `${k}:3`)
        : undefined,
    },
  );

  if (error) {
    throw new Error(`Deepgram transcription failed: ${error.message}`);
  }

  const transcript = extractTranscript(result);

  if (!transcript) {
    console.error(
      '[deepgram] Empty transcript for',
      buffer.length,
      'bytes, mimetype:',
      audioBlob.type,
    );
    throw new Error('Deepgram returned empty transcript');
  }

  return transcript;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function extractTranscript(response: DeepgramResponse): string {
  return (
    response.results?.channels?.[0]?.alternatives?.[0]?.transcript ?? ''
  );
}
