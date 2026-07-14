import { Skeleton, SkeletonLine } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function NewInterviewLoading() {
  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6 sm:py-10">
      <div className="text-center">
        <Skeleton className="mx-auto h-8 w-64" />
        <SkeletonLine className="mx-auto mt-2 h-4 w-48" />
      </div>
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex justify-between">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-6 w-24" />
          </div>
          <div className="flex gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-9 rounded-full" />
            ))}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}
