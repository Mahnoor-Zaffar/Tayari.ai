import { api } from "@/lib/api/client";

export interface UserAdmin {
  id: string;
  email: string;
  username: string;
  display_name: string;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  users: UserAdmin[];
  total: number;
  skip: number;
  limit: number;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
}

function buildQuery(params?: Record<string, string | number | undefined>): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(([, v]) => v !== undefined);
  if (!entries.length) return "";
  return "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

export const adminApi = {
  listUsers: (params?: { skip?: number; limit?: number; search?: string }) =>
    api.get<UserListResponse>(`/users${buildQuery(params)}`),

  getUser: (id: string) => api.get<UserAdmin>(`/users/${id}`),

  updateUser: (id: string, data: { display_name?: string; is_active?: boolean }) =>
    api.patch<UserAdmin>(`/users/${id}`, data),

  deleteUser: (id: string) => api.delete<{ deleted: boolean }>(`/users/${id}`),

  getStats: () => api.get<AdminStats>("/dashboard/admin"),
};
