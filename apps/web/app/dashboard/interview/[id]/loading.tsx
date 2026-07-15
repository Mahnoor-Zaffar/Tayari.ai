import { Skeleton } from "@/components/ui/skeleton";

export default function InterviewRoomLoading() {
  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col gap-4 p-4">
      <div className="flex items-center gap-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-48" />
        <Skeleton className="ml-auto h-4 w-16" />
      </div>
      <div className="flex flex-1 gap-4">
        <Skeleton className="flex-1 rounded-xl" />
        <Skeleton className="hidden w-72 rounded-xl sm:block" />
      </div>
    </div>
  );
}
