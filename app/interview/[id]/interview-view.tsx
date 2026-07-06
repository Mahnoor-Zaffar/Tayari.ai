'use client';

import { useCallback, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useInterviewStore } from '@/frontend/store/interview-store';
import { useMediaRecorder } from '@/frontend/hooks/useMediaRecorder';
import { SessionCard } from '@/frontend/components/interview/SessionCard';
import { StreamConsole } from '@/frontend/components/interview/StreamConsole';
import { MicButton } from '@/frontend/components/interview/MicButton';

export function InterviewView({ userId: defaultUserId }: { userId: string }) {
  const params = useParams();
  const sessionId = params.id as string;

  const {
    phase,
    setPhase,
    setTranscript,
    appendChunk,
    incrementTurnCount,
    resetToIdle,
    setError,
  } = useInterviewStore();

  const recorder = useMediaRecorder();

  useEffect(() => {
    useInterviewStore.getState().setSessionId(sessionId);
  }, [sessionId]);

  const sendAudio = useCallback(
    async (audioBlob: Blob) => {
      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('sessionId', sessionId);
        formData.append('userId', defaultUserId);

        const response = await fetch('/api/interview/turn', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Server error (${response.status})`);
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let hasStartedStreaming = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const frames = buffer.split('\n\n');
          buffer = frames.pop() ?? '';

          for (const frame of frames) {
            const lines = frame.split('\n');

            for (const line of lines) {
              if (!line.startsWith('DATA:')) continue;

              const rest = line.slice(5);
              const colonIdx = rest.indexOf(':');
              if (colonIdx === -1) continue;

              const type = rest.slice(0, colonIdx);
              const raw = rest.slice(colonIdx + 1);

              switch (type) {
                case 'TRANSCRIPT': {
                  const { text } = JSON.parse(raw);
                  setTranscript(text);
                  break;
                }

                case 'CHUNK': {
                  const { text } = JSON.parse(raw);
                  appendChunk(text);
                  if (!hasStartedStreaming) {
                    hasStartedStreaming = true;
                    setPhase('STREAMING_RESPONSE');
                  }
                  break;
                }

                case 'DONE': {
                  incrementTurnCount();
                  setTimeout(() => resetToIdle(), 1_500);
                  break;
                }

                case 'ERROR': {
                  const { message } = JSON.parse(raw);
                  setError(message);
                  break;
                }
              }
            }
          }
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Network request failed';
        setError(message);
      }
    },
    [sessionId, defaultUserId, setPhase, setTranscript, appendChunk, incrementTurnCount, resetToIdle, setError],
  );

  const handleToggleMic = useCallback(async () => {
    if (phase === 'IDLE') {
      try {
        await recorder.start();
        setPhase('RECORDING');
      } catch {
        setError('Could not start microphone');
      }
    } else if (phase === 'RECORDING') {
      setPhase('PROCESSING');
      try {
        const blob = await recorder.stop();
        await sendAudio(blob);
      } catch {
        setError('Audio capture failed');
        setPhase('IDLE');
      }
    }
  }, [phase, recorder, setPhase, setError, sendAudio]);

  useEffect(() => {
    return () => recorder.cleanup();
  }, [recorder]);

  return (
    <div className="flex h-screen bg-black text-zinc-100">
      <SessionCard />

      <div className="flex flex-1 flex-col">
        <StreamConsole />

        <div className="flex items-center justify-center border-t border-zinc-800 bg-zinc-950 px-6 py-5">
          <MicButton
            onToggle={handleToggleMic}
            isRecording={recorder.isRecording}
          />
        </div>
      </div>
    </div>
  );
}
