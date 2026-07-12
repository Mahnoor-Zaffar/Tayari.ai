# ADR-003: Password Hashing — bcrypt with Future Argon2 Migration

**Status:** Accepted  
**Date:** 2026-07-12  

## Context

User passwords must be stored using a computationally expensive, salt-inclusive hash algorithm. The project targets Argon2id (the OWASP-recommended algorithm), but the `argon2-cffi` package could not be installed in the current offline environment.

## Decision

1. **Current: bcrypt via `passlib[bcrypt]`** — rounds=12 (passlib default), automatic per-password salts.
2. **Future: Argon2id** — the `PasswordServiceProtocol` abstracts hashing behind `hash_password()` / `verify_password()` / `needs_rehash()`. When `argon2-cffi` is available, swap the implementation with zero service-layer changes.
3. **Automatic rehash on login** — `needs_rehash()` detects outdated algorithms/parameters; `login()` rehashes and persists the new hash transparently.

## Consequences

- Passwords are safe even if the `users` table is leaked.
- Migration to Argon2 is a single-file change + `pip install argon2-cffi`.
- `needs_rehash` ensures existing bcrypt hashes are upgraded to Argon2 on each user's next login.
