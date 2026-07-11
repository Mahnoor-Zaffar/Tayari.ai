import { createClient } from '@deepgram/sdk';

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY;

if (!DEEPGRAM_API_KEY) {
  throw new Error(
    'Deepgram configuration error: DEEPGRAM_API_KEY environment variable is not set. ' +
    'Please add DEEPGRAM_API_KEY=your_key to your .env.local file.',
  );
}

const deepgram = createClient(DEEPGRAM_API_KEY);

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

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export async function transcribeAudioBuffer(
  audioBuffer: Buffer,
  mimeType: string,
): Promise<string> {
  if (audioBuffer.length < 1024) {
    throw new Error(`Audio too small (${audioBuffer.length} bytes), skipping`);
  }

  try {
    const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
      audioBuffer,
      {
        model: 'nova-2',
        smart_format: true,
        punctuate: true,
        utterances: false,
        diarize: false,
        mimetype: mimeType || 'audio/webm;codecs=opus',
      },
    );

    if (error) {
      const status = 'status' in error ? (error as { status: number }).status : 0;

      if (status === 429) {
        console.error('[deepgram] Rate limited (429). Consider backing off.');
      } else if (status === 413) {
        console.error('[deepgram] Payload too large (413). Audio buffer size:', audioBuffer.length);
      } else {
        console.error('[deepgram] API error:', { status, message: error.message });
      }

      throw new Error(`Deepgram API error (${status}): ${error.message}`);
    }

    const transcript = extractTranscript(result);

    if (!transcript) {
      console.error(
        '[deepgram] Empty transcript for',
        audioBuffer.length,
        'bytes, mimetype:',
        mimeType,
      );
      throw new Error('Deepgram returned empty transcript');
    }

    return transcript;
  } catch (raw) {
    if (raw instanceof Error && raw.message.startsWith('Deepgram API error')) {
      throw raw;
    }

    const name = raw instanceof Error ? raw.name : typeof raw;
    const msg = raw instanceof Error ? raw.message : String(raw);
    console.error('[deepgram] Request failed:', { name, message: msg, bufferSize: audioBuffer.length });
    throw new Error(`Deepgram request failed: [${name}] ${msg}`);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function extractTranscript(response: DeepgramResponse): string {
  return (
    response.results?.channels?.[0]?.alternatives?.[0]?.transcript ?? ''
  );
}
