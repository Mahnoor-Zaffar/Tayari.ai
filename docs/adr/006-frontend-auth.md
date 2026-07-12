# ADR-006: Frontend Authentication Architecture

**Status:** Accepted  
**Date:** 2026-07-12  

## Context

The Next.js 15 frontend needs a secure, session-aware authentication layer that works with the backend's token-based auth (short-lived access token + long-lived refresh token with rotation).

## Decision

1. **Access token in React state (not localStorage)** — mitigates XSS risk. Stored in a `useState` inside `AuthProvider`.

2. **Refresh token in localStorage** — required for session persistence across page reloads. Key: `tayari_refresh_token`.

3. **Auth context** — `AuthProvider` provides `user`, `isLoading`, `isAuthenticated`, `login`, `register`, `logout` via React Context.

4. **Session restore** — on mount, if a refresh token exists, call `authApi.refresh()` to get a new access token + user data.

5. **401 interceptor** — `ApiClient._execute()` catches 401s, calls `_ensureFreshToken()` (which queues concurrent 401s), and retries the original request.

6. **Refresh bypasses interceptor** — `authApi.refresh()` uses raw `fetch` to avoid infinite retry loops when the refresh token itself is expired.

7. **Logout** — clears both tokens from state/localStorage, fires `authApi.logout()` (best-effort), redirects to `/auth/login`.

## Consequences

- Access tokens never persist in storage — XSS cannot steal a usable token.
- Refresh tokens in localStorage are still vulnerable to XSS, but the rotation + family-burn mechanism limits the damage window.
- Concurrent 401s are coalesced into a single refresh request.
- Session survives page reloads via the stored refresh token.
