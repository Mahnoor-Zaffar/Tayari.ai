'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useInterviewStore } from '@/frontend/store/interview-store';
import { useContinuousRecorder } from '@/frontend/hooks/useContinuousRecorder';
import { SessionCard } from '@/frontend/components/interview/SessionCard';
import { StreamConsole } from '@/frontend/components/interview/StreamConsole';
import { MicButton } from '@/frontend/components/interview/MicButton';
import { MAX_TURNS } from '@/types/interview';

export function InterviewView() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const {
    phase,
    setPhase,
    setTranscript,
    appendChunk,
    pushTurn,
    incrementTurnCount,
    resetToIdle,
    setError,
    setCompleted,
  } = useInterviewStore();

  const recorder = useContinuousRecorder();
  const sendingRef = useRef(false);
  const resumeRef = useRef(recorder.resume);
  resumeRef.current = recorder.resume;
  const responseTextRef = useRef('');
  const synthRef = useRef<SpeechSynthesis | null>(null);
  if (typeof window !== 'undefined') synthRef.current = window.speechSynthesis;

  function speakResponse(text: string) {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 0.7;
    synthRef.current.speak(utterance);
  }

  function cancelSpeech() {
    synthRef.current?.cancel();
  }

  const [showInstructions, setShowInstructions] = useState(false);

  useEffect(() => {
    useInterviewStore.getState().setSessionId(sessionId);
    const seen = localStorage.getItem('tayari_instructions_seen');
    if (!seen) setShowInstructions(true);
    return () => cancelSpeech();
  }, [sessionId]);

  function dismissInstructions() {
    localStorage.setItem('tayari_instructions_seen', '1');
    setShowInstructions(false);
  }

  const processSSEStream = useCallback(
    async (response: Response, isEndCall: boolean) => {
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let hasStartedStreaming = false;
      let autoEnd = false;

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
                responseTextRef.current += text;
                appendChunk(text);
                if (!hasStartedStreaming) {
                  hasStartedStreaming = true;
                  setPhase('STREAMING_RESPONSE');
                }
                break;
              }

              case 'DONE': {
                const doneData = JSON.parse(raw);
                console.log('[interview] DONE data:', JSON.stringify(doneData));
                console.log('[interview] turnCount after increment:', useInterviewStore.getState().turnCount + 1);
                pushTurn(doneData.candidateResponse, doneData.interviewerQuestion);
                incrementTurnCount();
                if (doneData.completed) {
                  recorder.stop();
                  setCompleted();
                  setTimeout(() => router.push(`/interview/${sessionId}/report`), 3_000);
                } else if (!isEndCall && useInterviewStore.getState().turnCount >= MAX_TURNS) {
                  autoEnd = true;
                  recorder.stop();
                  setPhase('PROCESSING');
                } else {
                  speakResponse(responseTextRef.current);
                  setTimeout(() => {
                    resetToIdle();
                    resumeRef.current();
                  }, 1_500);
                }
                responseTextRef.current = '';
                break;
              }

              case 'ERROR': {
                const { message } = JSON.parse(raw);
                setError(message);
                setTimeout(() => {
                  resumeRef.current();
                }, 1_500);
                break;
              }
            }
          }
        }
      }

      return autoEnd;
    },
    [sessionId, setPhase, setTranscript, appendChunk, pushTurn, incrementTurnCount, resetToIdle, setError, recorder, router],
  );

  const sendEndRequest = useCallback(async () => {
    const formData = new FormData();
    formData.append('end', 'true');
    formData.append('sessionId', sessionId);

    const response = await fetch('/api/interview/turn', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(`Server error (${response.status}): ${body.slice(0, 200)}`);
    }

    await processSSEStream(response, true);
  }, [sessionId, processSSEStream]);

  const sendAudio = useCallback(
    async (audioBlob: Blob) => {
      if (sendingRef.current) return;
      sendingRef.current = true;
      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('sessionId', sessionId);

        const response = await fetch('/api/interview/turn', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const body = await response.text().catch(() => '');
          throw new Error(`Server error (${response.status}): ${body.slice(0, 200)}`);
        }

        const autoEnd = await processSSEStream(response, false);

        if (autoEnd) {
          await sendEndRequest();
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Network request failed';
        setError(message);
      } finally {
        sendingRef.current = false;
      }
    },
    [sessionId, sendEndRequest, processSSEStream],
  );

  // Called by VAD when silence >3s detected
  const onChunkReady = useCallback(
    async (blob: Blob) => {
      cancelSpeech();
      setPhase('PROCESSING');
      await sendAudio(blob);
    },
    [setPhase, sendAudio],
  );

  const handleToggleMic = useCallback(async () => {
    if (phase === 'IDLE') {
      try {
        await recorder.start(onChunkReady);
        setPhase('LISTENING');
      } catch {
        setError('Could not start microphone');
      }
    } else if (phase === 'LISTENING') {
      recorder.stop();
      setPhase('IDLE');
    }
  }, [phase, recorder, onChunkReady, setPhase, setError]);

  const handleSkip = useCallback(async () => {
    if (sendingRef.current) return;
    sendingRef.current = true;
    setPhase('PROCESSING');
    try {
      const formData = new FormData();
      formData.append('skip', 'true');
      formData.append('sessionId', sessionId);

      const response = await fetch('/api/interview/turn', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const body = await response.text().catch(() => '');
        throw new Error(`Server error (${response.status}): ${body.slice(0, 200)}`);
      }

      const autoEnd = await processSSEStream(response, false);

      if (autoEnd) {
        await sendEndRequest();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Skip request failed';
      setError(message);
    } finally {
      sendingRef.current = false;
    }
  }, [sessionId, processSSEStream, sendEndRequest, setPhase, setError]);

  const handleEnd = useCallback(async () => {
    if (sendingRef.current) return;
    sendingRef.current = true;
    setPhase('PROCESSING');
    try {
      await sendEndRequest();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'End interview failed';
      setError(message);
    } finally {
      sendingRef.current = false;
    }
  }, [sendEndRequest, setPhase, setError]);

  return (
    <>
      {showInstructions && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4">
          <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-900 p-6 shadow-2xl">
            <h2 className="text-lg font-semibold text-zinc-100">How the Interview Works</h2>

            <div className="mt-4 space-y-3 text-sm text-zinc-400">
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-900/50 text-xs font-bold text-emerald-400">1</span>
                <span><strong className="text-zinc-200">Speak naturally</strong> — the mic detects your voice automatically. No buttons needed.</span>
              </div>
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-900/50 text-xs font-bold text-emerald-400">2</span>
                <span><strong className="text-zinc-200">Pause to send</strong> — after ~3s of silence, your answer is sent to the AI.</span>
              </div>
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-900/50 text-xs font-bold text-emerald-400">3</span>
                <span><strong className="text-zinc-200">AI responds</strong> — you will hear the response spoken aloud while text appears.</span>
              </div>
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-900/50 text-xs font-bold text-emerald-400">4</span>
                <span><strong className="text-zinc-200">Skip or End</strong> — use the buttons to skip a question or end the interview early.</span>
              </div>
            </div>

            <div className="mt-1 text-xs text-zinc-600">
              16 questions across Intro, Technical, Behavioral, and Wrap-up stages.
            </div>

            <button
              onClick={dismissInstructions}
              className="mt-5 w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500"
            >
              Got it
            </button>
          </div>
        </div>
      )}

    <div className="flex h-screen bg-black text-zinc-100">
      {phase !== 'COMPLETE' && <SessionCard />}

      <div className="flex flex-1 flex-col">
        <StreamConsole />

        {phase === 'COMPLETE' ? (
          <div className="flex flex-col items-center justify-center gap-4 border-t border-zinc-800 bg-zinc-950 px-6 py-8">
            <div className="text-lg font-semibold text-emerald-400">Interview Complete</div>
            <div className="text-sm text-zinc-400">Redirecting to report...</div>
          </div>
        ) : (
          <div className="flex items-center justify-center border-t border-zinc-800 bg-zinc-950 px-6 py-5">
            <MicButton
              onToggle={handleToggleMic}
              onSkip={handleSkip}
              onEnd={handleEnd}
              isRecording={recorder.isListening}
              stream={recorder.stream}
            />
          </div>
        )}
      </div>
    </div>
    </>
  );
}
