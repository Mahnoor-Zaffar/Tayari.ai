import { createClient } from '@deepgram/sdk';

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

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const arrayBuffer = await audioBlob.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);

  if (buffer.length < 1024) {
    throw new Error(`Audio too small (${buffer.length} bytes), skipping`);
  }

  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    buffer,
    {
      model: 'nova-2',
      mimetype: audioBlob.type || 'audio/webm;codecs=opus',
      smart_format: true,
      punctuate: true,
      filler_words: true,
    },
  );

  if (error) {
    throw new Error(`Deepgram transcription failed: ${error.message}`);
  }

  const transcript = extractTranscript(result);

  if (!transcript) {
    console.error('[deepgram] Empty transcript for', buffer.length, 'bytes, mimetype:', audioBlob.type);
    throw new Error('Deepgram returned empty transcript');
  }

  return transcript;
}

function extractTranscript(
  response: DeepgramResponse,
): string {
  return (
    response.results?.channels?.[0]?.alternatives?.[0]?.transcript ?? ''
  );
}
