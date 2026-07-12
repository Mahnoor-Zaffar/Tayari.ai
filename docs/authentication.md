# Authentication — Architecture & Reference

## Architecture

The auth system follows a strict **layered** pattern with dependency inversion at
every boundary.  No layer reaches across another — each depends only on the layer
beneath it or on an abstract protocol.

```
┌─────────────────────────────────────────────────────┐
│                     HTTP Layer                       │
│  routes.py · guard.py · schemas.py · main.py        │
│  (FastAPI routers, request/response, middleware)     │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│  services.py  (AuthenticationService)               │
│  (business rules, orchestration — zero SQL/HTTP)    │
├────────────────────────┬────────────────────────────┤
│   Domain / Protocol    │     Infrastructure          │
│   interfaces.py        │   jwt/service.py            │
│   domain/user.py       │   password/service.py       │
│   jwt/models.py        │   repositories.py           │
│   jwt/interfaces.py    │   models.py (ORM)           │
│   exceptions.py        │                             │
└────────────────────────┴────────────────────────────┘
```

### Dependency Injection

All three external dependencies are injected into `AuthenticationService` via
its constructor:

```
AuthenticationService
  ├── UserRepositoryProtocol  ───> UserRepository (SQLAlchemy)
  ├── PasswordServiceProtocol ───> PasswordService (bcrypt)
  └── TokenServiceProtocol    ───> TokenService (JWT / python-jose)
```

FastAPI's `Depends` (`features/auth/dependencies.py`) wires them together at
runtime.  Tests replace any layer with a mock or an in-memory variant without
changing a single line of production code.

### Guard Layer

Three FastAPI dependencies sit between the HTTP layer and the route handlers:

| Dependency | Purpose |
|---|---|
| `get_current_user` | Extracts `Authorization: Bearer <access_token>`, verifies the JWT, looks up the DB record, returns a `CurrentUser`.  Raises 401 / 403 on failure. |
| `get_optional_user` | Same as above but returns `None` instead of raising — for routes that work differently for authenticated vs anonymous users. |
| `RoleChecker("admin", ...)` / `PermissionChecker("users:write", ...)` | Callable class guards: verify the current user's roles/permissions include at least one of the specified values.  Raises 403 otherwise. |

### Error Hierarchy

All HTTP errors inherit from `AppError(HTTPException)` and serialise to:

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid email or password"
  },
  "request_id": "a1b2c3d4-..."
}
```

| HTTP Code | Error Class | Error Code | When |
|---|---|---|---|
| 401 | `AuthenticationError` | `UNAUTHORIZED` | Missing/invalid credentials |
| 401 | `InvalidTokenError` | `INVALID_TOKEN` | Token expired, revoked, or wrong type |
| 403 | `AuthorizationError` | `FORBIDDEN` | Authenticated but not allowed |
| 404 | `NotFoundError` | `NOT_FOUND` | User not found after token decode |
| 409 | `ConflictError` | `CONFLICT` | Duplicate email or username |
| 422 | `ValidationError` | `VALIDATION_ERROR` | Schema validation failure |
| 429 | `RateLimitedError` | `RATE_LIMITED` | Too many requests |
| 500 | `DatabaseError` / `InternalError` | `DATABASE_ERROR` / `INTERNAL_ERROR` | Server-side failure |

---

## Folder Structure

```
features/auth/
├── __init__.py
├── dependencies.py            # FastDI wiring (get_auth_service, get_token_service)
├── exceptions.py              # Domain exceptions (InvalidCredentialsError, etc.)
├── guard.py                   # get_current_user, get_optional_user, RoleChecker, PermissionChecker
├── interfaces.py              # Protocols: UserRepositoryProtocol, PasswordServiceProtocol, TokenServiceProtocol
├── models.py                  # SQLAlchemy ORM model (User table)
├── repositories.py            # UserRepository (find_by_id, create_user, etc.)
├── routes.py                  # FastAPI router — all /auth/* endpoints
├── schemas.py                 # Pydantic request/response models
├── services.py                # AuthenticationService — business rules
├── domain/
│   ├── __init__.py
│   └── user.py                # Domain User model (Pydantic, no SQLAlchemy dependency)
├── jwt/
│   ├── __init__.py
│   ├── config.py              # JWTConfig — secret, algorithm, TTLs, issuer, audience
│   ├── interfaces.py          # TokenBlacklistProtocol
│   ├── models.py              # TokenPayload — verified token claims
│   └── service.py             # TokenService — create, verify, revoke, peek, revoke_family
├── password/
│   ├── __init__.py
│   └── service.py             # PasswordService — hash, verify, needs_rehash (bcrypt)
└── tests/
    ├── __init__.py
    ├── conftest.py             # Shared fixtures (db_engine, session, repository)
    ├── test_auth_service.py    # Unit tests — AuthenticationService with mocks
    ├── test_auth_routes.py     # Integration — route handlers with mocked service
    ├── test_auth_guard.py      # Integration — guard layer (current user, role/permission checkers)
    ├── test_audit.py           # Unit + integration — AuditEvent, AuditLogger, middleware
    ├── test_coverage_fillers.py# Edge cases for error classes, TokenPayload validation
    ├── test_integration_auth_flow.py  # Full E2E: signup→login→refresh→logout, password reset
    ├── test_password_service.py       # Unit — bcrypt hash/verify/needs_rehash edge cases
    ├── test_token_service.py          # Unit — JWT create/verify/revoke/peek, reuse detection
    └── test_user_repository.py        # Integration — CRUD, soft-delete, exists
```

Global infra:

```
core/
├── audit.py          # AuthEvent enum, AuditEvent, AuditLogger, auth_audit_middleware
├── errors.py         # AppError hierarchy (+ ErrorCode constants)
└── logging.py        # request_id contextvar, get_logger, setup_logging
```

---

## Endpoints

All routes are prefixed with `/api/v1`.

### `POST /auth/signup`

Register a new user account.

**Request**
```json
{
  "email": "alice@example.com",
  "username": "alice",
  "display_name": "Alice Smith",
  "password": "strong-password-123"
}
```

**Validation rules**
| Field | Constraints |
|---|---|
| `email` | Valid email format (`EmailStr`) |
| `username` | 3–50 chars, letters / digits / underscore only |
| `display_name` | 1–100 chars |
| `password` | ≥ 8 characters |

**Response `201`**
```json
{
  "success": true,
  "data": {
    "access_token": "<jwt>",
    "refresh_token": "<jwt>",
    "token_type": "bearer",
    "user": {
      "id": "<uuid>",
      "email": "alice@example.com",
      "username": "alice",
      "display_name": "Alice Smith",
      "email_verified": false,
      "created_at": "2026-01-01T00:00:00Z"
    }
  }
}
```

**Errors**
- `409 CONFLICT` — Email or username already taken
- `422 VALIDATION_ERROR` — Schema validation failure

**Audit event**: `register`

---

### `POST /auth/login`

Authenticate with email and password.

**Request**
```json
{
  "email": "alice@example.com",
  "password": "strong-password-123"
}
```

**Response `200`** — Same shape as signup.

**Errors**
- `401 UNAUTHORIZED` — Invalid email or password
- `403 FORBIDDEN` — Account is disabled
- `422 VALIDATION_ERROR` — Schema validation failure

**Audit events**: `login` (success), `login_failed` (failure)

---

### `POST /auth/refresh`

Issue a new access + refresh token pair using a valid refresh token.  The old
refresh token is **revoked** (rotation).  If a revoked token is reused, the
entire token family is burned.

**Request**
```json
{
  "refresh_token": "<jwt>"
}
```

**Response `200`** — Same shape as signup.

**Errors**
- `401 INVALID_TOKEN` — Token expired, revoked, or wrong type
- `404 NOT_FOUND` — User referenced by token no longer exists
- `403 FORBIDDEN` — User account is disabled

**Audit events**: `token_refreshed` (success), `token_refresh_rejected` (replay)

---

### `POST /auth/logout`

Revoke the current refresh token.

**Request**
```json
{
  "refresh_token": "<jwt>"
}
```

**Response `200`**
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

**Errors**
- `401 INVALID_TOKEN` — Token is invalid or expired

**Audit event**: `logout`

---

### `POST /auth/forgot-password`

Send a password-reset link to the given email.  Returns the same response
whether or not the email exists (prevents enumeration).

**Request**
```json
{
  "email": "alice@example.com"
}
```

**Response `200`**
```json
{
  "success": true,
  "data": {
    "message": "If an account with that email exists, a reset link has been sent"
  }
}
```

**Audit event**: `password_reset_requested`

---

### `POST /auth/reset-password`

Complete a password reset by providing the token (received via email) and a
new password.

**Request**
```json
{
  "token": "<jwt>",
  "new_password": "new-strong-password-456"
}
```

**Response `200`**
```json
{
  "success": true,
  "data": {
    "message": "Password has been reset successfully"
  }
}
```

**Errors**
- `401 INVALID_TOKEN` — Reset token expired or invalid
- `403 FORBIDDEN` — User account is disabled
- `404 NOT_FOUND` — User no longer exists

**Audit event**: `password_reset_completed`

---

## Security

### JWT Token Design

All tokens are signed JWTs (HS256) with the following standard claims:

| Claim | Value | Purpose |
|---|---|---|
| `sub` | User UUID | Identifies the user |
| `type` | `"access"` / `"refresh"` / `"email_verify"` / `"password_reset"` | Prevents token type confusion |
| `exp` | Expiration timestamp | Limits token lifetime |
| `iat` | Issued-at timestamp | Freshness anchor |
| `jti` | Random UUID | Unique token ID for revocation |
| `iss` | `"tayari-ai"` | Identifies this service as issuer |
| `aud` | `"tayari-api"` | Scopes the token to this API |
| `roles` / `permissions` | `list[str]` | Authorization claims (access tokens only) |
| `token_family` | UUID | Groups refresh tokens for family-level revocation |

TTLs are configured per token type via `JWTConfig`:

| Token Type | TTL |
|---|---|
| Access | 15 minutes |
| Refresh | 7 days |
| Email verify | 24 hours |
| Password reset | 1 hour |

### Refresh-Token Rotation & Reuse Detection

```
1. Client sends refresh_token "A" (family: F)
2. Server verifies "A", issues "B" (same family F)
3. Server revokes "A" (marks jti as blacklisted)
4. Attacker replays "A"
   → Server rejects "A" (jti is blacklisted)
   → Server extracts token_family F via peek()
   → Server calls revoke_family(F)
   → "B" (and any other token in family F) is now dead
```

This means a stolen refresh token is useful **once** — the attacker gets one
response, but the legitimate user is forced to re-authenticate.

### Password Hashing

- **Algorithm**: bcrypt (work factor 12 — ~2¹² iterations)
- **Salt**: Generated internally by bcrypt, embedded in the hash string
- **Rehash detection**: `needs_rehash()` compares the stored work factor against
  the current configuration — allows gradual factor upgrades without forcing
  password resets
- **Argon2-ready**: The architecture is identical; swap `PasswordService` for an
  Argon2 implementation when the library is available

### Auditing

Every auth event is logged to the `auth.audit` logger as a structured JSON
record with the following fields:

| Field | Description |
|---|---|
| `ts` | ISO 8601 timestamp |
| `event` | Event type (`register`, `login`, `login_failed`, etc.) |
| `user_id` | User UUID (when known) |
| `email_hash` | SHA-256 prefix (first 16 hex chars) — never the full address |
| `ip` | Client IP (from `X-Forwarded-For` or `client.host`) |
| `user_agent` | `User-Agent` header value |
| `request_id` | UUID correlated with the HTTP request |
| `outcome` | `"success"` or `"failure"` |
| `reason` | Failure reason (only on failure) |

**Never logged**: passwords, raw tokens, password hashes, full email addresses.

The `auth_audit_middleware` extracts IP and User-Agent once per request and
attaches an `AuditLogger` to `request.state.audit`.

### Token Revocation

TokenService supports an optional `TokenBlacklistProtocol` backend.  When
configured:

- `verify()` checks the blacklist before accepting a token
- `revoke()` adds the token's `jti` to the blacklist with its original expiry
- `revoke_family()` adds `"family:{token_family}"` to the blacklist, killing
  every token in the family

Pluggable implementations:
- **In-memory** (used in tests)
- **Redis** (recommended for production — TTL-aligned key expiry)

---

## Database

### Schema: `users` table

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    display_name    VARCHAR(100) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    email_verified  BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX ix_users_email        ON users (email);
CREATE INDEX ix_users_username     ON users (username);
CREATE INDEX ix_users_active_scope ON users (is_active, deleted_at);
CREATE INDEX ix_users_created_at   ON users (created_at);
```

### Soft Delete

Users are soft-deleted (`deleted_at` set, `is_active` = `false`) rather than
physically removed.  Queries exclude soft-deleted records by default through the
`_active_query()` helper in `UserRepository`.  The `include_deleted=True`
parameter overrides this when needed (e.g. during token refresh where a deleted
user should not be silently re-activated).

---

## Flow Diagrams

### Registration Flow

```
Client                  FastAPI                 AuthenticationService        UserRepository        TokenService
  │                        │                           │                        │                     │
  │  POST /auth/signup     │                           │                        │                     │
  │───────────────────────>│                           │                        │                     │
  │                        │  RegisterRequest          │                        │                     │
  │                        │──────────────────────────>│                        │                     │
  │                        │                           │  exists(email)         │                     │
  │                        │                           │───────────────────────>│                     │
  │                        │                           │<───────────────────────│                     │
  │                        │                           │  exists(username)      │                     │
  │                        │                           │───────────────────────>│                     │
  │                        │                           │<───────────────────────│                     │
  │                        │                           │                        │                     │
  │                        │                           │  hash_password(pw)     │                     │
  │                        │                           │  (PasswordService)     │                     │
  │                        │                           │                        │                     │
  │                        │                           │  create_user(data)     │                     │
  │                        │                           │───────────────────────>│                     │
  │                        │                           │<───────────────────────│                     │
  │                        │                           │                        │                     │
  │                        │                           │  create_access_token   │                     │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │<──────────────────────────────────────────────│
  │                        │                           │  create_refresh_token  │                     │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │<──────────────────────────────────────────────│
  │                        │  AuthResult               │                        │                     │
  │                        │<──────────────────────────│                        │                     │
  │  201 + tokens          │                           │                        │                     │
  │<───────────────────────│                           │                        │                     │
```

### Login + Refresh Rotation Flow

```
Client                  FastAPI                 AuthenticationService        UserRepository        TokenService
  │                        │                           │                        │                     │
  │  POST /auth/login      │                           │                        │                     │
  │───────────────────────>│  LoginRequest               │                        │                     │
  │                        │──────────────────────────>│                        │                     │
  │                        │                           │  find_by_email         │                     │
  │                        │                           │───────────────────────>│                     │
  │                        │                           │<───────────────────────│                     │
  │                        │                           │  verify_password       │                     │
  │                        │                           │  (PasswordService)     │                     │
  │                        │                           │                        │                     │
  │                        │                           │  create_access_token   │                     │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │<──────────────────────────────────────────────│
  │                        │                           │  create_refresh_token  │                     │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │<──────────────────────────────────────────────│
  │                        │<──────────────────────────│                        │                     │
  │  200 + tokens          │                           │                        │                     │
  │<───────────────────────│                           │                        │                     │
  │                        │                           │                        │                     │
  │  ── Later ──           │                           │                        │                     │
  │                        │                           │                        │                     │
  │  POST /auth/refresh    │                           │                        │                     │
  │───────────────────────>│  RefreshRequest            │                        │                     │
  │                        │──────────────────────────>│                        │                     │
  │                        │                           │  verify(token,"refresh")│                    │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │<──────────────────────────────────────────────│
  │                        │                           │  revoke(old_token)     │                     │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │                        │                     │
  │                        │                           │  find_by_id            │                     │
  │                        │                           │───────────────────────>│                     │
  │                        │                           │<───────────────────────│                     │
  │                        │                           │                        │                     │
  │                        │                           │  create_access_token   │                     │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │<──────────────────────────────────────────────│
  │                        │                           │  create_refresh_token  │                     │
  │                        │                           │  (same token_family)   │                     │
  │                        │                           │──────────────────────────────────────────────>│
  │                        │                           │<──────────────────────────────────────────────│
  │                        │<──────────────────────────│                        │                     │
  │  200 + new tokens      │                           │                        │                     │
  │<───────────────────────│                           │                        │                     │
```

### Reuse Detection (Replay Attack)

```
Attacker                 Server                              Legitimate User
  │                        │                                       │
  │  Replay old token      │                                       │
  │───────────────────────>│                                       │
  │                        │  verify(old_token)                    │
  │                        │  └── jti is blacklisted → INVALID     │
  │                        │  peek(old_token)                      │
  │                        │  └── extract token_family             │
  │                        │  revoke_family(token_family)          │
  │                        │  └── family:F → blacklisted           │
  │                        │                                       │
  │  401 INVALID_TOKEN     │                                       │
  │<───────────────────────│                                       │
  │                        │                                       │
  │                        │                                       │  Try replacement token
  │                        │<──────────────────────────────────────│
  │                        │  verify(replacement)                  │
  │                        │  └── family:F blacklisted → INVALID   │
  │                        │                                       │
  │                        │  401 INVALID_TOKEN                    │
  │                        │──────────────────────────────────────>│
```

---

## Future Improvements

1. **Redis-backed token blacklist** — `TokenBlacklistProtocol` implementation
   using Redis with TTL-aligned key expiry (auto-cleanup).  The interface
   already exists; only the implementation is missing.

2. **Rate limiting** — Integrate with the `RateLimitedError` class.  Apply
   per-IP and per-email throttling to login and forgot-password endpoints to
   prevent brute-force and enumeration attacks.

3. **Email delivery** — The `forgot_password` service method creates a
   password-reset token but does not send it.  Wire it to `Resend` (or any SMTP
   provider) using the `RESEND_API_KEY` setting.

4. **Asymmetric signing (RS256)** — Switch from HS256 to RS256 so the public
   key can be served via a JWKS endpoint, enabling third-party verification of
   tokens (e.g. a microservice that only needs the public key, not the secret).

5. **Email verification** — The `/auth/signup` route returns `email_verified:
   false`.  Implement the `/auth/verify-email` endpoint and send a verification
   email at signup time.

6. **Session management UI** — Allow users to view and revoke active sessions
   (refresh tokens) from their profile page.

7. **OAuth2 / social login** — Extend the protocol layer to support Google,
   GitHub, or any OAuth2 provider.  The `TokenServiceProtocol` is already
   designed for OAuth2-style claims (iss, aud, scoped roles/permissions).

8. **Security headers** — Add `Strict-Transport-Security`,
   `X-Content-Type-Options`, `X-Frame-Options`, and `Content-Security-Policy`
   headers to all responses.

9. **Audit log storage** — Route the `auth.audit` logger to a persistent store
   (e.g. a dedicated database table, S3, or a SIEM system) for compliance and
   forensics.

10. **Account lockout** — Track consecutive failed login attempts per email / IP
    and temporarily lock the account after N failures.
