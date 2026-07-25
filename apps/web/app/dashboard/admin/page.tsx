"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Users, Activity, UserX } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { useAdminStats } from "@/features/admin/hooks/use-admin";

export default function AdminDashboardPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { data: stats, isLoading } = useAdminStats();

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.push("/dashboard");
    }
  }, [authLoading, isAdmin, router]);

  if (authLoading || !isAdmin) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">System-wide overview</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {isLoading ? (
          <>
            {Array.from({ length: 3 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="flex flex-col items-center gap-1 py-4 text-center">
                  <Skeleton className="h-5 w-5 rounded-full" />
                  <Skeleton className="mt-1 h-7 w-12" />
                  <Skeleton className="mt-1 h-3 w-20" />
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <>
            <StatCard icon={Users} label="Total Users" value={stats?.total_users ?? 0} />
            <StatCard icon={Activity} label="Active Users" value={stats?.active_users ?? 0} />
            <StatCard icon={UserX} label="Inactive Users" value={stats?.inactive_users ?? 0} />
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-1 py-4 text-center">
        <Icon className="h-5 w-5 text-muted-foreground" />
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}
