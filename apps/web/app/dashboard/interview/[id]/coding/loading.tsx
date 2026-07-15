import { Skeleton } from "@/components/ui/skeleton";

export default function CodingLoading() {
  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col gap-4 p-4">
      <div className="flex gap-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-8 w-48" />
      </div>
      <div className="flex flex-1 gap-4">
        <Skeleton className="hidden w-80 rounded-xl sm:block" />
        <Skeleton className="flex-1 rounded-xl" />
      </div>
      <div className="h-40 rounded-xl bg-muted" />
      <div className="flex justify-end gap-2">
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
  );
}
