"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  authApi,
  type AuthResponse,
  type AuthUser,
  type LoginInput,
  type RegisterInput,
} from "@/lib/api/auth";
import { configureAuth } from "@/lib/api/client";

// ── Storage keys ───────────────────────────────────────────────────────────

const REFRESH_KEY = "tayari_refresh_token";

// ──── Helpers ───────────────────────────────────────────────────────────

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

function storeRefreshToken(token: string) {
  localStorage.setItem(REFRESH_KEY, token);
}

function clearRefreshToken() {
  localStorage.removeItem(REFRESH_KEY);
}

// ── Context shape ──────────────────────────────────────────────────────────

interface AuthContextValue {
  /** The current user, or ``null`` while loading or when unauthenticated. */
  user: AuthUser | null;
  /** The current access token, or ``null`` if not authenticated. */
  accessToken: string | null;
  /** Whether the initial session-restore check has finished. */
  isLoading: boolean;
  /** ``true`` once a user is available. */
  isAuthenticated: boolean;
  /** Authenticate with email + password. */
  login: (input: LoginInput) => Promise<AuthResponse>;
  /** Create a new account. */
  register: (input: RegisterInput) => Promise<AuthResponse>;
  /** End the session — clears tokens, redirects to login. */
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ───────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const initialized = useRef(false);

  // ── Refresh session (called by API client interceptor AND restore) ────

  const refreshSession = useCallback(async (): Promise<string> => {
    const token = getRefreshToken();
    if (!token) throw new Error("No refresh token");

    const result = await authApi.refresh(token);
    storeRefreshToken(result.refresh_token);
    setAccessToken(result.access_token);
    setUser(result.user);
    return result.access_token;
  }, []);

  // ── Auth failure handler (called by API client interceptor) ──────────

  const logout = useCallback(() => {
    clearRefreshToken();
    setAccessToken(null);
    setUser(null);
    authApi.logout().catch(() => {});
    window.location.href = "/auth/login";
  }, []);

  // ── Wire the API client interceptor on first render ──────────────────

  useEffect(() => {
    configureAuth({
      getAccessToken: () => accessToken,
      refreshSession,
      onAuthFailure: logout,
    });
  }, [accessToken, refreshSession, logout]);

  // ── Restore session on mount ─────────────────────────────────────────

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      setIsLoading(false);
      return;
    }

    refreshSession()
      .catch(() => {
        clearRefreshToken();
        setAccessToken(null);
        setUser(null);
      })
      .finally(() => setIsLoading(false));
    // Run only once — the refreshSession ref is stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Login ────────────────────────────────────────────────────────────

  const login = useCallback(async (input: LoginInput) => {
    const result = await authApi.login(input);
    storeRefreshToken(result.refresh_token);
    setAccessToken(result.access_token);
    setUser(result.user);
    return result;
  }, []);

  // ── Register ─────────────────────────────────────────────────────────

  const register = useCallback(async (input: RegisterInput) => {
    const result = await authApi.signup(input);
    storeRefreshToken(result.refresh_token);
    setAccessToken(result.access_token);
    setUser(result.user);
    return result;
  }, []);

  // ── Memoised context value ───────────────────────────────────────────

  const value = useMemo(
    () => ({
      user,
      accessToken,
      isLoading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
    }),
    [user, accessToken, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ── Hook ───────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
