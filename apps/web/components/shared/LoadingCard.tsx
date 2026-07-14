import { cn } from "@/lib/utils";
import { SkeletonCard } from "@/components/ui/skeleton";

interface LoadingCardProps {
  lines?: number;
  className?: string;
}

export function LoadingCard({ className }: LoadingCardProps) {
  return <SkeletonCard className={cn("bg-card", className)} />;
}
