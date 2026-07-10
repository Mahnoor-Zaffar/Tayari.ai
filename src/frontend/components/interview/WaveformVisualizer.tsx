'use client';

import { useEffect, useRef, useState } from 'react';

const BAR_COUNT = 24;
const SPEECH_THRESHOLD = 6;
const THROTTLE_FRAMES = 4;

interface BarState {
  levels: number[];
  isSpeech: boolean;
}

interface WaveformVisualizerProps {
  stream: MediaStream | null;
}

export function WaveformVisualizer({ stream }: WaveformVisualizerProps) {
  const [barState, setBarState] = useState<BarState>({
    levels: Array(BAR_COUNT).fill(0),
    isSpeech: false,
  });

  const isSpeechRef = useRef(false);
  const frameRef = useRef(0);

  useEffect(() => {
    if (!stream) {
      setBarState({ levels: Array(BAR_COUNT).fill(0), isSpeech: false });
      return;
    }

    const audioContext = new AudioContext();
    if (audioContext.state === 'suspended') audioContext.resume();
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
      const currentIsSpeech = currentRms >= SPEECH_THRESHOLD;

      frameRef.current++;
      const shouldPaintBars = frameRef.current % THROTTLE_FRAMES === 0;
      const speechChanged = currentIsSpeech !== isSpeechRef.current;

      if (shouldPaintBars || speechChanged) {
        isSpeechRef.current = currentIsSpeech;

        const chunkSize = Math.floor(timeData.length / BAR_COUNT);
        const barHeights = Array.from({ length: BAR_COUNT }, (_, i) => {
          let chunkSum = 0;
          for (let j = 0; j < chunkSize; j++) {
            chunkSum += Math.abs((timeData[i * chunkSize + j] ?? 128) - 128);
          }
          return Math.min(1, chunkSum / (chunkSize * 64));
        });

        setBarState({ levels: barHeights, isSpeech: currentIsSpeech });
      }

      animId = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      cancelAnimationFrame(animId);
      audioContext.close();
    };
  }, [stream]);

  const { levels, isSpeech } = barState;

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
