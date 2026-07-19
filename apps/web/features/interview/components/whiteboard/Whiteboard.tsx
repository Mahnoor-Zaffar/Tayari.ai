"use client";

import { memo, useCallback, useRef, useState, useEffect } from "react";
import {
  MousePointer2, Square, Circle, Minus, Type, Trash2, Undo2,
  Download, Palette,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Tool = "select" | "rect" | "circle" | "line" | "text";

interface Point { x: number; y: number }

interface Shape {
  id: string;
  tool: Tool;
  start: Point;
  end: Point;
  color: string;
  width: number;
  text?: string;
}

interface WhiteboardProps {
  className?: string;
  onExport?: (dataUrl: string) => void;
}

const COLORS = ["#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#8b5cf6", "#000000", "#ffffff"];
const DEFAULT_COLOR = "#000000";

export const Whiteboard = memo(function Whiteboard({ className, onExport }: WhiteboardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tool, setTool] = useState<Tool>("rect");
  const [color, setColor] = useState(DEFAULT_COLOR);
  const [width, setWidth] = useState(2);
  const [shapes, setShapes] = useState<Shape[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [startPos, setStartPos] = useState<Point | null>(null);
  const [textInput, setTextInput] = useState<{ pos: Point; value: string } | null>(null);
  const shapeIdRef = useRef(0);
  const canvasElRef = useRef<HTMLCanvasElement>(null);

  const getPos = useCallback((e: React.MouseEvent<HTMLCanvasElement>): Point => {
    const canvas = canvasElRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }, []);

  const drawShapes = useCallback(() => {
    const canvas = canvasElRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw grid (light dots)
    ctx.fillStyle = "#e5e7eb";
    for (let x = 0; x < canvas.width; x += 30) {
      for (let y = 0; y < canvas.height; y += 30) {
        ctx.beginPath();
        ctx.arc(x, y, 1, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    for (const shape of shapes) {
      ctx.strokeStyle = shape.color;
      ctx.lineWidth = shape.width;
      ctx.fillStyle = shape.color + "15";

      const x = Math.min(shape.start.x, shape.end.x);
      const y = Math.min(shape.start.y, shape.end.y);
      const w = Math.abs(shape.end.x - shape.start.x);
      const h = Math.abs(shape.end.y - shape.start.y);

      if (shape.id === selectedId) {
        ctx.setLineDash([5, 5]);
      }

      switch (shape.tool) {
        case "rect":
          ctx.fillRect(x, y, w, h);
          ctx.strokeRect(x, y, w, h);
          break;
        case "circle":
          const cx = (shape.start.x + shape.end.x) / 2;
          const cy = (shape.start.y + shape.end.y) / 2;
          const rx = w / 2;
          const ry = h / 2;
          ctx.beginPath();
          ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
          break;
        case "line":
          ctx.beginPath();
          ctx.moveTo(shape.start.x, shape.start.y);
          ctx.lineTo(shape.end.x, shape.end.y);
          ctx.stroke();
          break;
        case "text":
          if (shape.text) {
            ctx.font = "14px sans-serif";
            ctx.fillStyle = shape.color;
            ctx.fillText(shape.text, shape.start.x, shape.start.y);
          }
          break;
      }

      if (shape.id === selectedId) {
        ctx.setLineDash([]);
      }
    }

    // Draw in-progress shape
    if (drawing && startPos) {
      const current = { x: 0, y: 0 }; // will be updated in mousemove
    }
  }, [shapes, selectedId, drawing, startPos]);

  useEffect(() => {
    drawShapes();
  }, [drawShapes]);

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getPos(e);

    if (tool === "select") {
      // Find clicked shape (reverse order)
      const clicked = [...shapes].reverse().find((s) => {
        if (s.tool === "text") {
          return Math.abs(pos.x - s.start.x) < 50 && Math.abs(pos.y - s.start.y) < 15;
        }
        const x = Math.min(s.start.x, s.end.x);
        const y = Math.min(s.start.y, s.end.y);
        const w = Math.abs(s.end.x - s.start.x);
        const h = Math.abs(s.end.y - s.start.y);
        return pos.x >= x && pos.x <= x + w && pos.y >= y && pos.y <= y + h;
      });
      setSelectedId(clicked?.id ?? null);
      return;
    }

    if (tool === "text") {
      const id = `shape-${shapeIdRef.current++}`;
      const newShape: Shape = { id, tool, start: pos, end: pos, color, width };
      setShapes((prev) => [...prev, newShape]);
      setSelectedId(id);
      setTextInput({ pos, value: "" });
      return;
    }

    setDrawing(true);
    setStartPos(pos);
  }, [tool, getPos, shapes, color, width]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing || !startPos) return;
    const pos = getPos(e);
    const canvas = canvasElRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Redraw with preview
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Grid
    ctx.fillStyle = "#e5e7eb";
    for (let x = 0; x < canvas.width; x += 30) {
      for (let y = 0; y < canvas.height; y += 30) {
        ctx.beginPath();
        ctx.arc(x, y, 1, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Draw all shapes
    for (const shape of shapes) {
      ctx.strokeStyle = shape.color;
      ctx.lineWidth = shape.width;
      ctx.fillStyle = shape.color + "15";
      const x = Math.min(shape.start.x, shape.end.x);
      const y = Math.min(shape.start.y, shape.end.y);
      const w = Math.abs(shape.end.x - shape.start.x);
      const h = Math.abs(shape.end.y - shape.start.y);
      switch (shape.tool) {
        case "rect": ctx.fillRect(x, y, w, h); ctx.strokeRect(x, y, w, h); break;
        case "circle": {
          const cx = (shape.start.x + shape.end.x) / 2;
          const cy = (shape.start.y + shape.end.y) / 2;
          ctx.beginPath(); ctx.ellipse(cx, cy, w / 2, h / 2, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
          break;
        }
        case "line": ctx.beginPath(); ctx.moveTo(shape.start.x, shape.start.y); ctx.lineTo(shape.end.x, shape.end.y); ctx.stroke(); break;
      }
    }

    // Draw preview
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.fillStyle = color + "15";
    const x = Math.min(startPos.x, pos.x);
    const y = Math.min(startPos.y, pos.y);
    const w = Math.abs(pos.x - startPos.x);
    const h = Math.abs(pos.y - startPos.y);
    switch (tool) {
      case "rect": ctx.fillRect(x, y, w, h); ctx.strokeRect(x, y, w, h); break;
      case "circle": {
        const cx = (startPos.x + pos.x) / 2;
        const cy = (startPos.y + pos.y) / 2;
        ctx.beginPath(); ctx.ellipse(cx, cy, w / 2, h / 2, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        break;
      }
      case "line": ctx.beginPath(); ctx.moveTo(startPos.x, startPos.y); ctx.lineTo(pos.x, pos.y); ctx.stroke(); break;
    }
  }, [drawing, startPos, getPos, shapes, color, width, tool]);

  const handleMouseUp = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing || !startPos) return;
    const pos = getPos(e);
    const id = `shape-${shapeIdRef.current++}`;
    const newShape: Shape = { id, tool: tool as Tool, start: startPos, end: pos, color, width };
    setShapes((prev) => [...prev, newShape]);
    setDrawing(false);
    setStartPos(null);
  }, [drawing, startPos, getPos, tool, color, width]);

  const handleDelete = useCallback(() => {
    if (!selectedId) return;
    setShapes((prev) => prev.filter((s) => s.id !== selectedId));
    setSelectedId(null);
  }, [selectedId]);

  const handleUndo = useCallback(() => {
    setShapes((prev) => prev.slice(0, -1));
    setSelectedId(null);
  }, []);

  const handleClear = useCallback(() => {
    setShapes([]);
    setSelectedId(null);
  }, []);

  const handleExport = useCallback(() => {
    const canvas = canvasElRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL("image/png");
    onExport?.(dataUrl);
    const link = document.createElement("a");
    link.download = "architecture.png";
    link.href = dataUrl;
    link.click();
  }, [onExport]);

  const handleTextSubmit = useCallback(() => {
    if (!textInput || !textInput.value.trim()) {
      setTextInput(null);
      return;
    }
    setShapes((prev) =>
      prev.map((s) =>
        s.id === selectedId ? { ...s, text: textInput.value } : s
      )
    );
    setTextInput(null);
  }, [textInput, selectedId]);

  return (
    <div className={cn("flex flex-col overflow-hidden rounded-lg border border-border bg-card", className)}>
      {/* Toolbar */}
      <div className="flex items-center gap-1 border-b border-border px-2 py-1.5">
        <ToolButton icon={MousePointer2} active={tool === "select"} onClick={() => setTool("select")} label="Select" />
        <ToolButton icon={Square} active={tool === "rect"} onClick={() => setTool("rect")} label="Rectangle" />
        <ToolButton icon={Circle} active={tool === "circle"} onClick={() => setTool("circle")} label="Circle" />
        <ToolButton icon={Minus} active={tool === "line"} onClick={() => setTool("line")} label="Line" />
        <ToolButton icon={Type} active={tool === "text"} onClick={() => setTool("text")} label="Text" />
        <div className="mx-1 h-5 w-px bg-border" />
        <div className="flex items-center gap-0.5">
          {COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setColor(c)}
              className={cn("h-5 w-5 rounded-full border-2", color === c ? "border-foreground" : "border-transparent")}
              style={{ backgroundColor: c }}
              aria-label={`Color ${c}`}
            />
          ))}
        </div>
        <div className="mx-1 h-5 w-px bg-border" />
        <input
          type="range" min={1} max={8} value={width}
          onChange={(e) => setWidth(Number(e.target.value))}
          className="h-1 w-16" aria-label="Stroke width"
        />
        <div className="ml-auto flex items-center gap-1">
          {selectedId && (
            <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={handleDelete} aria-label="Delete">
              <Trash2 className="h-3.5 w-3.5 text-destructive" />
            </Button>
          )}
          <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={handleUndo} aria-label="Undo">
            <Undo2 className="h-3.5 w-3.5" />
          </Button>
          <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={handleClear} aria-label="Clear">
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
          <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={handleExport} aria-label="Export PNG">
            <Download className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative flex-1 overflow-hidden bg-white">
        <canvas
          ref={canvasElRef}
          width={800}
          height={600}
          className="h-full w-full cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        />

        {/* Text input overlay */}
        {textInput && (
          <div
            className="absolute"
            style={{ left: textInput.pos.x, top: textInput.pos.y - 20 }}
          >
            <input
              autoFocus
              type="text"
              value={textInput.value}
              onChange={(e) => setTextInput({ ...textInput, value: e.target.value })}
              onBlur={handleTextSubmit}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleTextSubmit();
                if (e.key === "Escape") setTextInput(null);
              }}
              className="rounded border border-primary bg-white px-1 py-0.5 text-sm shadow-sm outline-none"
              placeholder="Type..."
              aria-label="Text input"
            />
          </div>
        )}
      </div>
    </div>
  );
});

function ToolButton({ icon: Icon, active, onClick, label }: {
  icon: React.ComponentType<{ className?: string }>;
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:bg-accent",
        active && "bg-accent text-foreground",
      )}
      aria-label={label}
      title={label}
    >
      <Icon className="h-3.5 w-3.5" />
    </button>
  );
}
