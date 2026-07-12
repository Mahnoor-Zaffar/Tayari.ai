from datetime import timedelta

from pydantic import BaseModel


class JWTConfig(BaseModel):
    """Self-contained JWT configuration, independent of the global settings.

    Can be instantiated directly or populated from any source — env vars,
    ``core.config.Settings``, or a secrets manager. This satisfies the
    "store configuration separately" requirement.
    """

    # ── Key material ──────────────────────────────────────────────────────
    # For HS256: a high-entropy secret (min 32 bytes recommended).
    # For RS256: the PEM-encoded RSA private key.  If ``PUBLIC_KEY`` is
    # provided it is used for verification; otherwise ``SECRET_KEY`` is
    # used for both signing and verification (HS256-only).
    SECRET_KEY: str = "change-me-in-production"
    PUBLIC_KEY: str | None = None

    # ── Algorithm ─────────────────────────────────────────────────────────
    # HS256 is the safe default for single-service deployments.
    # Switch to RS256 in production when you need third-party verification
    # of tokens (e.g. JWKS endpoint, OAuth compatibility).
    ALGORITHM: str = "HS256"

    # ── Time-to-live per token type ───────────────────────────────────────
    # Access tokens:  15 minutes — short window limits leaked-token damage.
    # Refresh tokens: 7 days — traded for new access tokens; rotated on use.
    # Email verify:   24 hours — enough for a user to check their inbox.
    # Password reset: 1 hour   — short window limits brute-force or leaked-link risk.
    ACCESS_TOKEN_TTL: timedelta = timedelta(minutes=15)
    REFRESH_TOKEN_TTL: timedelta = timedelta(days=7)
    EMAIL_VERIFY_TTL: timedelta = timedelta(hours=24)
    PASSWORD_RESET_TTL: timedelta = timedelta(hours=1)

    # ── Claims ────────────────────────────────────────────────────────────
    # ``iss`` identifies this service as the token authority.
    # ``aud`` scopes the token to this API — a token minted for ``tayari-api``
    #        is rejected by ``tayari-admin`` (OAuth readiness).
    ISSUER: str = "tayari-ai"
    AUDIENCE: str = "tayari-api"
