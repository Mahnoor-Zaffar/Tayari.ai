"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface RadarChartProps {
  dimensions: Array<{ key: string; label: string; score: number }>;
  className?: string;
}

const SIZE = 180;
const CENTER = SIZE / 2;
const RADIUS = 75;

function polygonPoints(values: number[], sides: number): string {
  return values
    .map((val, i) => {
      const angle = (Math.PI * 2 * i) / sides - Math.PI / 2;
      const r = (val / 5) * RADIUS;
      return `${CENTER + r * Math.cos(angle)},${CENTER + r * Math.sin(angle)}`;
    })
    .join(" ");
}

const LABEL_RADIUS = RADIUS + 20;

export const RadarChart = memo(function RadarChart({ dimensions, className }: RadarChartProps) {
  if (dimensions.length === 0) return null;

  const sides = dimensions.length;
  const scores = dimensions.map((d) => d.score);
  const points = polygonPoints(scores, sides);

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <svg
        width={SIZE + 50}
        height={SIZE + 50}
        viewBox={`0 0 ${SIZE + 50} ${SIZE + 50}`}
        className="overflow-visible"
      >
        {/* Background grid */}
        {[1, 2, 3, 4, 5].map((level) => (
          <polygon
            key={level}
            points={polygonPoints(
              dimensions.map(() => level),
              sides,
            )}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth={0.5}
            opacity={0.3}
          />
        ))}
        {/* Data polygon */}
        <motion.polygon
          points={polygonPoints(
            dimensions.map(() => 0),
            sides,
          )}
          animate={{ points }}
          transition={{ duration: 1, ease: "easeOut" }}
          fill="hsl(var(--primary) / 0.15)"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
        />
        {/* Labels */}
        {dimensions.map((dim, i) => {
          const angle = (Math.PI * 2 * i) / sides - Math.PI / 2;
          const x = CENTER + LABEL_RADIUS * Math.cos(angle) + 25;
          const y = CENTER + LABEL_RADIUS * Math.sin(angle) + 25;
          return (
            <text
              key={dim.key}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-current text-[9px] text-muted-foreground"
            >
              {dim.label}
            </text>
          );
        })}
      </svg>
    </div>
  );
});
