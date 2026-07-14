import { cn } from "@/lib/utils";

/* ── Base primitive ─────────────────────────────────────────────────── */

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-skeleton rounded-md bg-muted", className)} {...props} />;
}

/* ── Variants ───────────────────────────────────────────────────────── */

interface SkeletonLineProps {
  width?: string;
  className?: string;
}

export function SkeletonLine({ width = "w-full", className }: SkeletonLineProps) {
  return <Skeleton className={cn("h-4", width, className)} />;
}

interface SkeletonTextProps {
  lines?: number;
  className?: string;
}

export function SkeletonText({ lines = 3, className }: SkeletonTextProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine key={i} width={i === lines - 1 ? "w-3/4" : "w-full"} />
      ))}
    </div>
  );
}

interface SkeletonAvatarProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const avatarSizes = {
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-12 w-12",
};

export function SkeletonAvatar({ size = "md", className }: SkeletonAvatarProps) {
  return <Skeleton className={cn("rounded-full shrink-0", avatarSizes[size], className)} />;
}

interface SkeletonImageProps {
  className?: string;
}

export function SkeletonImage({ className }: SkeletonImageProps) {
  return <Skeleton className={cn("aspect-video w-full rounded-lg", className)} />;
}

/* ── Card skeletons ─────────────────────────────────────────────────── */

interface SkeletonCardProps {
  className?: string;
}

export function SkeletonCard({ className }: SkeletonCardProps) {
  return (
    <div className={cn("rounded-xl border bg-card p-5 shadow-sm", className)}>
      <SkeletonLine width="w-1/3" className="mb-3" />
      <Skeleton className="mb-2 h-8 w-1/4" />
      <SkeletonLine width="w-2/3" />
    </div>
  );
}

export function SkeletonStatCard({ className }: SkeletonCardProps) {
  return (
    <div className={cn("rounded-xl border bg-card p-5 shadow-sm", className)}>
      <SkeletonLine width="w-20" className="mb-3" />
      <Skeleton className="mb-1 h-8 w-12" />
      <SkeletonLine width="w-28" />
    </div>
  );
}

interface SkeletonWidgetCardProps {
  lines?: number;
  className?: string;
}

export function SkeletonWidgetCard({ lines = 3, className }: SkeletonWidgetCardProps) {
  return (
    <div className={cn("rounded-xl border bg-card p-5 shadow-sm", className)}>
      <div className="mb-4 flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="space-y-1.5">
          <SkeletonLine width="w-24" />
          <SkeletonLine width="w-32" />
        </div>
      </div>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine key={i} width={i === lines - 1 ? "w-2/3" : "w-full"} className="mt-2" />
      ))}
    </div>
  );
}

export function SkeletonActivityItem({ className }: SkeletonCardProps) {
  return (
    <div className={cn("flex items-center gap-4 rounded-lg border p-4", className)}>
      <SkeletonAvatar size="md" />
      <div className="flex-1 space-y-1.5">
        <SkeletonLine width="w-32" />
        <SkeletonLine width="w-24" />
      </div>
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  );
}
