// =============================================================================
// Tayari.ai — Deepgram Speech-to-Text Service
// Model: Nova-2  |  Latency target: <300ms
// =============================================================================

import { createClient, type PrerecordedTranscriptionResponse } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const arrayBuffer = await audioBlob.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);

  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    buffer,
    {
      model: 'nova-2',
      mimetype: 'audio/webm;codecs=opus',
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
    throw new Error('Deepgram returned empty transcript');
  }

  return transcript;
}

function extractTranscript(
  response: PrerecordedTranscriptionResponse,
): string {
  return (
    response.results?.channels?.[0]?.alternatives?.[0]?.transcript ?? ''
  );
}
