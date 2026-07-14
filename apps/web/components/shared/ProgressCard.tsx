import { cn } from "@/lib/utils";

interface ProgressCardProps {
  label: string;
  value: number;
  max: number;
  description?: string;
  color?: "primary" | "success" | "warning";
  className?: string;
}

const barColors = {
  primary: "bg-primary",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
};

export function ProgressCard({
  label,
  value,
  max,
  description,
  color = "primary",
  className,
}: ProgressCardProps) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;

  return (
    <div className={cn("rounded-xl border bg-card p-4 shadow-sm", className)}>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-muted-foreground">
          {value}/{max}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
          className={cn("h-full rounded-full transition-all duration-500", barColors[color])}
          style={{ width: `${pct}%` }}
        />
      </div>
      {description && <p className="mt-1.5 text-xs text-muted-foreground">{description}</p>}
    </div>
  );
}
