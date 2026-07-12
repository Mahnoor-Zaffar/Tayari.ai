import { api } from "./client"
import type { ApiResponse } from "./client"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

// ── Types ──────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string
  email: string
  username: string
  display_name: string
  email_verified: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: AuthUser
}

export interface LoginInput {
  email: string
  password: string
}

export interface RegisterInput {
  email: string
  username: string
  display_name: string
  password: string
}

export interface ForgotPasswordInput {
  email: string
}

// ── API calls ──────────────────────────────────────────────────────────────

export const authApi = {
  login: (data: LoginInput) => api.post<AuthResponse>("/auth/login", data),

  signup: (data: RegisterInput) => api.post<AuthResponse>("/auth/signup", data),

  logout: () => api.post<void>("/auth/logout"),

  forgotPassword: (data: ForgotPasswordInput) => api.post<void>("/auth/forgot-password", data),

  me: () => api.get<AuthUser>("/users/me"),

  /** Refresh tokens — uses raw fetch to bypass the API client's 401 interceptor,
   *  avoiding infinite retry when the refresh token itself is expired. */
  refresh: async (refreshToken: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    const json: ApiResponse<AuthResponse> = await response.json()

    if (!json.success) {
      throw new Error(json.error?.message ?? "Token refresh failed")
    }

    return json.data as AuthResponse
  },
}
