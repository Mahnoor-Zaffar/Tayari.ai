"use client";

import { use, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/features/auth/hooks/use-auth";
import { useUser, useUpdateUser, useDeleteUser } from "@/features/admin/hooks/use-admin";

export default function AdminUserDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { data: user, isLoading, isError, error, refetch } = useUser(id);
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.push("/dashboard");
    }
  }, [authLoading, isAdmin, router]);

  if (authLoading || !isAdmin) return null;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 rounded-xl" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16" role="alert">
        <div className="rounded-full bg-destructive/10 p-3">
          <AlertCircle className="h-6 w-6 text-destructive" />
        </div>
        <p className="text-lg font-medium">Failed to load user</p>
        <p className="text-sm text-muted-foreground">
          {error instanceof Error ? error.message : "An unexpected error occurred."}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" /> Retry
          </Button>
          <Link href="/dashboard/admin/users">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/users">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">{user.display_name}</h1>
          <p className="text-sm text-muted-foreground">{user.email}</p>
        </div>
        <Badge variant={user.is_active ? "success" : "secondary"} className="ml-auto">
          {user.is_active ? "Active" : "Inactive"}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>User Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <DetailRow label="ID" value={user.id} />
          <DetailRow label="Username" value={user.username} />
          <DetailRow label="Email" value={user.email} />
          <DetailRow label="Email Verified" value={user.email_verified ? "Yes" : "No"} />
          <DetailRow label="Created" value={new Date(user.created_at).toLocaleString()} />
          <DetailRow label="Updated" value={new Date(user.updated_at).toLocaleString()} />
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button
          variant={user.is_active ? "secondary" : "default"}
          onClick={() => updateUser.mutate({ id, data: { is_active: !user.is_active } })}
          disabled={updateUser.isPending}
        >
          {user.is_active ? "Deactivate" : "Activate"}
        </Button>
        <Button
          variant="secondary"
          className="text-destructive hover:text-destructive"
          onClick={() => {
            if (confirm(`Delete user "${user.display_name}"? This cannot be undone.`)) {
              deleteUser.mutate(id, {
                onSuccess: () => router.push("/dashboard/admin/users"),
              });
            }
          }}
          disabled={deleteUser.isPending}
        >
          Delete User
        </Button>
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="w-32 text-xs font-medium text-muted-foreground">{label}</span>
      <span className="text-sm break-all">{value}</span>
    </div>
  );
}
