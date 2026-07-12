const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

interface ApiOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE"
  body?: unknown
  headers?: Record<string, string>
}

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: unknown[]
  }
  request_id?: string
}

// ── Auth hooks (set by configureAuth) ──────────────────────────────────────

let _getAccessToken: () => string | null = () => null
let _refreshSession: () => Promise<string> = () => Promise.reject(new Error("auth not configured"))
let _onAuthFailure: () => void = () => {}

export function configureAuth(config: {
  getAccessToken: () => string | null
  refreshSession: () => Promise<string>
  onAuthFailure: () => void
}) {
  _getAccessToken = config.getAccessToken
  _refreshSession = config.refreshSession
  _onAuthFailure = config.onAuthFailure
}

// ── Concurrent refresh queue ───────────────────────────────────────────────

let _isRefreshing = false
let _refreshQueue: Array<{ resolve: () => void; reject: (err: unknown) => void }> = []

function _flushQueue(err?: unknown) {
  for (const entry of _refreshQueue) {
    err ? entry.reject(err) : entry.resolve()
  }
  _refreshQueue = []
}

async function _ensureFreshToken(): Promise<boolean> {
  if (!_isRefreshing) {
    _isRefreshing = true
    try {
      await _refreshSession()
      _flushQueue()
      return true
    } catch (err) {
      _flushQueue(err)
      _onAuthFailure()
      return false
    } finally {
      _isRefreshing = false
    }
  }

  // Another refresh is in-flight — wait for it
  await new Promise<void>((resolve, reject) => {
    _refreshQueue.push({ resolve, reject })
  })
  return true
}

// ── ApiClient ──────────────────────────────────────────────────────────────

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async request<T>(path: string, options: ApiOptions = {}): Promise<T> {
    return this._execute<T>(path, options, 0)
  }

  private async _execute<T>(path: string, options: ApiOptions, attempt: number): Promise<T> {
    const token = _getAccessToken()
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...options.headers,
    }
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body != null ? JSON.stringify(options.body) : undefined,
    })

    // ── Silent refresh on 401 ──────────────────────────────────────────
    if (response.status === 401 && token && attempt === 0) {
      const refreshed = await _ensureFreshToken()
      if (refreshed) {
        return this._execute<T>(path, options, attempt + 1)
      }
    }

    const json: ApiResponse<T> = await response.json()

    if (!json.success) {
      throw new ApiError(
        json.error?.code ?? "UNKNOWN",
        json.error?.message ?? "Unknown error",
        response.status,
        json.error?.details,
        json.request_id,
      )
    }

    return json.data as T
  }

  get<T>(path: string) {
    return this.request<T>(path)
  }

  post<T>(path: string, body?: unknown) {
    return this.request<T>(path, { method: "POST", body })
  }

  patch<T>(path: string, body?: unknown) {
    return this.request<T>(path, { method: "PATCH", body })
  }

  delete<T>(path: string) {
    return this.request<T>(path, { method: "DELETE" })
  }
}

// ── ApiError ───────────────────────────────────────────────────────────────

class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details?: unknown[],
    public requestId?: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

// ── Singleton ──────────────────────────────────────────────────────────────

export const api = new ApiClient(API_BASE)
export { ApiError }
export type { ApiResponse }
