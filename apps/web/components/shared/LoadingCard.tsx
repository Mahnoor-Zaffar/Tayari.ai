import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface LoadingCardProps {
  lines?: number;
  className?: string;
}

export function LoadingCard({ lines = 3, className }: LoadingCardProps) {
  return (
    <div className={cn("rounded-xl border bg-card p-5 shadow-sm", className)}>
      <Skeleton className="mb-3 h-4 w-24" />
      <Skeleton className="mb-2 h-8 w-16" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="mt-2 h-3 w-full" />
      ))}
    </div>
  );
}
