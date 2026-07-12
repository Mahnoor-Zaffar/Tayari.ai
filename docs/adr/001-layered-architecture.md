# ADR-001: Layered Architecture for Authentication

**Status:** Accepted  
**Date:** 2026-07-12  

## Context

The auth subsystem touches persistence (SQL), cryptographic operations (JWT, hashing), HTTP transport (FastAPI), and business rules. Without clear boundaries, these concerns entangle, making the system hard to test, audit, or swap implementations.

## Decision

We adopt a five-layer architecture with strict dependency direction:

```
┌──────────────────────────────────┐
│         routes (HTTP)            │  ← FastAPI router, request/response only
├──────────────────────────────────┤
│       services (orchestration)   │  ← Business rules, no SQL or HTTP
├──────────────────────────────────┤
│      interfaces (protocols)      │  ← Abstract contracts (Protocol classes)
├──────────────────────────────────┤
│  repositories / jwt / password   │  ← Concrete implementations
├──────────────────────────────────┤
│         domain (models)          │  ← Pure data: User, UserCreate, etc.
└──────────────────────────────────┘
```

- **Routes** (`features/auth/routes.py`): parse HTTP, call service, return JSON.
- **Services** (`features/auth/services.py`): business rules — pure orchestration, no database or HTTP knowledge.
- **Interfaces** (`features/auth/interfaces.py`): `Protocol` classes (`UserRepositoryProtocol`, `PasswordServiceProtocol`, `TokenServiceProtocol`) enabling test doubles.
- **Repositories** (`features/auth/repositories.py`): SQLAlchemy implementation of `UserRepositoryProtocol`.
- **Domain** (`features/auth/domain/user.py`): `User`, `UserCreate`, `UserUpdate` — plain Pydantic/SQLAlchemy models.

## Consequences

- Each layer is independently testable with mocks/stubs.
- Swapping password hashing (bcrypt → Argon2) or token backend (local → JWKS) requires zero changes to services.
- Slight boilerplate from Protocol definitions, but they serve as living documentation.
