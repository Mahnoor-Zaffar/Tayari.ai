# ADR-004: Error Handling — Standardised Error Shape and Hierarchy

**Status:** Accepted  
**Date:** 2026-07-12  

## Context

All API errors must return a consistent JSON shape so clients (frontend, third-party integrations) can handle errors generically. FastAPI's default error responses vary by source (validation errors, HTTPExceptions, database errors).

## Decision

1. **Standard response shape:**
   ```json
   {
     "success": false,
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "Human-readable summary",
       "details": []  // optional, machine-readable
     },
     "request_id": "uuid"
   }
   ```

2. **Exception hierarchy** — all application exceptions inherit from `AppError(HTTPException)`:
   - `ValidationError` (422)
   - `AuthenticationError` (401)
   - `TokenError` (401) — distinct from AuthenticationError
   - `AuthorizationError` (403)
   - `NotFoundError` (404)
   - `ConflictError` (409)
   - `RateLimitedError` (429)
   - `DatabaseError` (500)
   - `InternalError` (500)

3. **Global handlers** — registered in `main.py` for `AppError`, `RequestValidationError`, `HTTPException`, `IntegrityError`, `SQLAlchemyError`, and catch-all `Exception`.

4. **`success_response()` helper** — builds `{"success": true, "data": {...}}`.

## Consequences

- Frontend can parse errors uniformly via `getErrorDetails()` / `getErrorMessage()`.
- New error types extend `AppError` with zero boilerplate.
- `request_id` on every error enables log correlation.
- TokenError vs AuthenticationError lets clients distinguish "no credentials" (redirect to login) from "credentials expired" (silent refresh).
