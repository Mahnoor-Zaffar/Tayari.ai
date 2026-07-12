# ADR-002: JWT Design — Typed Tokens with Rotation and Family-Level Revocation

**Status:** Accepted  
**Date:** 2026-07-12  

## Context

Auth requires multiple token kinds (access, refresh, email verification, password reset) with different lifetimes and security properties. Refresh tokens must support rotation to limit the window of stolen-token misuse.

## Decision

1. **Typed tokens** — every JWT carries a `type` claim (`access`, `refresh`, `email_verify`, `password_reset`). `verify()` enforces the expected type. An access token cannot be used as a refresh token.

2. **Standard claims** — `sub` (user UUID), `exp`, `iat`, `jti` (unique ID for revocation), `iss`, `aud`, plus `type` and optional `roles`/`permissions`/`token_family`.

3. **Refresh-token rotation** — `refresh()` revokes the old token before issuing new ones. The new refresh token inherits the same `token_family`.

4. **Family-level burn** — if a revoked refresh token is reused, `peek()` extracts its `token_family` and `revoke_family()` blacklists the entire family, killing any subsequent tokens from the same rotation chain.

5. **Revocation backend** — `TokenBlacklistProtocol` interface. Currently no-op (no Redis), but the architecture is in place.

6. **Peek without verification** — `peek()` uses `jwt.get_unverified_claims()` for logging/telemetry only; never for access decisions.

## Consequences

- Stolen refresh tokens are useless after rotation.
- Replay detection burns the entire family, minimising the window of compromise.
- Token types prevent cross-use (e.g., a password-reset token cannot authorise API calls).
- Revocation requires Redis to be functional; graceful degradation when Redis is unavailable (revocation silently no-ops).
