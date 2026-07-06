'use client';

import { useEffect, useRef, useState } from 'react';

const BAR_COUNT = 16;

interface WaveformVisualizerProps {
  stream: MediaStream | null;
}

export function WaveformVisualizer({ stream }: WaveformVisualizerProps) {
  const [levels, setLevels] = useState<number[]>(Array(BAR_COUNT).fill(0));
  const ctxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (!stream) {
      setLevels(Array(BAR_COUNT).fill(0));
      return;
    }

    const audioContext = new AudioContext();
    ctxRef.current = audioContext;
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let animId: number;

    const tick = () => {
      analyser.getByteFrequencyData(dataArray);
      const downsampled = Array.from({ length: BAR_COUNT }, (_, i) => {
        const chunkSize = Math.floor(dataArray.length / BAR_COUNT);
        let sum = 0;
        for (let j = 0; j < chunkSize; j++) {
          sum += dataArray[i * chunkSize + j] ?? 0;
        }
        return Math.min(1, sum / (chunkSize * 255));
      });
      setLevels(downsampled);
      animId = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      cancelAnimationFrame(animId);
      audioContext.close();
      ctxRef.current = null;
    };
  }, [stream]);

  return (
    <div className="flex items-end justify-center gap-[3px] h-8 w-24">
      {levels.map((level, i) => (
        <div
          key={i}
          className="w-[5px] bg-red-400 rounded-t transition-all duration-75"
          style={{ height: `${Math.max(3, level * 32)}px`, opacity: Math.max(0.15, level) }}
        />
      ))}
    </div>
  );
}
