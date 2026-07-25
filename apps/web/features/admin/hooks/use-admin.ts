import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi, type UserAdmin } from "@/features/admin/api/admin";

export function useAdminStats() {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => adminApi.getStats(),
    staleTime: 30_000,
  });
}

export function useUsers(params?: { skip?: number; limit?: number; search?: string }) {
  return useQuery({
    queryKey: ["admin", "users", params],
    queryFn: () => adminApi.listUsers(params),
    staleTime: 10_000,
  });
}

export function useUser(id: string) {
  return useQuery({
    queryKey: ["admin", "user", id],
    queryFn: () => adminApi.getUser(id),
    enabled: !!id,
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: { display_name?: string; is_active?: boolean };
    }) => adminApi.updateUser(id, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["admin", "user", variables.id] });
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => adminApi.deleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
      qc.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
}
