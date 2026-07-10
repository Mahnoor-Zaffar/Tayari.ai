'use client';

import { useEffect, useRef, useState } from 'react';

const BAR_COUNT = 24;
const SPEECH_THRESHOLD = 6;

interface WaveformVisualizerProps {
  stream: MediaStream | null;
}

export function WaveformVisualizer({ stream }: WaveformVisualizerProps) {
  const [levels, setLevels] = useState<number[]>(Array(BAR_COUNT).fill(0));
  const [rms, setRms] = useState(0);
  const ctxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (!stream) {
      setLevels(Array(BAR_COUNT).fill(0));
      setRms(0);
      return;
    }

    const audioContext = new AudioContext();
    ctxRef.current = audioContext;
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    const timeData = new Uint8Array(analyser.frequencyBinCount);
    let animId: number;

    const tick = () => {
      analyser.getByteTimeDomainData(timeData);
      const sum = timeData.reduce((acc, v) => acc + Math.abs(v - 128), 0);
      const currentRms = sum / timeData.length;
      setRms(currentRms);

      const barHeights = Array.from({ length: BAR_COUNT }, (_, i) => {
        const chunkSize = Math.floor(timeData.length / BAR_COUNT);
        let chunkSum = 0;
        for (let j = 0; j < chunkSize; j++) {
          chunkSum += Math.abs((timeData[i * chunkSize + j] ?? 128) - 128);
        }
        return Math.min(1, chunkSum / (chunkSize * 64));
      });
      setLevels(barHeights);
      animId = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      cancelAnimationFrame(animId);
      audioContext.close();
      ctxRef.current = null;
    };
  }, [stream]);

  const isSpeech = rms >= SPEECH_THRESHOLD;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="flex items-end justify-center gap-[2px] h-12 w-36">
        {levels.map((level, i) => (
          <div
            key={i}
            className="w-[4px] rounded-t transition-all duration-75"
            style={{
              height: `${Math.max(2, level * 48)}px`,
              backgroundColor: isSpeech
                ? `hsl(${120 - level * 40}, 80%, ${50 + level * 20}%)`
                : `rgb(${80 + level * 60}, ${80 + level * 40}, ${80 + level * 30})`,
              opacity: Math.max(0.2, level + 0.15),
            }}
          />
        ))}
      </div>
      <span className={`text-[10px] font-medium tracking-wider ${isSpeech ? 'text-emerald-400' : 'text-zinc-500'}`}>
        {isSpeech ? 'SPEAKING' : 'LISTENING'}
      </span>
    </div>
  );
}
