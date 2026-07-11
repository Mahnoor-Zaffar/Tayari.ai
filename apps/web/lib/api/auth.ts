import { api } from "./client"
import type { SignupInput, LoginInput, User } from "@tayari/types"

export const authApi = {
  signup: (data: SignupInput) => api.post<User>("/auth/signup", data),
  login: (data: LoginInput) => api.post<{ token: string; user: User }>("/auth/login", data),
  logout: () => api.post<void>("/auth/logout"),
  me: () => api.get<User>("/users/me"),
}
