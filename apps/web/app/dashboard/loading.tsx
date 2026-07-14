import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      {/* Welcome card skeleton */}
      <Skeleton className="h-28 w-full rounded-xl" />

      {/* Stats grid skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border bg-card p-5 shadow-sm">
            <Skeleton className="mb-3 h-4 w-20" />
            <Skeleton className="mb-1 h-8 w-12" />
            <Skeleton className="h-3 w-28" />
          </div>
        ))}
      </div>

      {/* Quick actions skeleton */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>

      {/* Two-column layout skeleton */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-2 lg:col-span-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
        <div className="space-y-6">
          <Skeleton className="h-44 rounded-xl" />
          <Skeleton className="h-44 rounded-xl" />
        </div>
      </div>
    </div>
  );
}
