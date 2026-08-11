"""Startup validation of critical configuration values."""

import logging
import sys

from core.config import settings

log = logging.getLogger("app.bootstrap")


def validate_prod_settings() -> None:
    """Exit on startup if production-critical settings are insecure."""
    errors: list[str] = []

    if settings.ENVIRONMENT == "production":
        if settings.JWT_SECRET_KEY == "change-me-in-production":
            errors.append("JWT_SECRET_KEY must be changed in production")

        if settings.JWT_ALGORITHM not in ("RS256", "ES256", "ES384", "ES512"):
            log.warning("JWT_ALGORITHM=%s is not asymmetric; consider RS256 for production", settings.JWT_ALGORITHM)

        if not settings.RESEND_API_KEY:
            log.warning("RESEND_API_KEY is not set — password reset emails will not be sent")

        if not settings.DATABASE_URL or settings.DATABASE_URL.startswith("postgresql+asyncpg://tayari:tayari_dev@"):
            log.warning("DATABASE_URL appears to be the development default — verify it is correct")

        # CORS must not allow wildcard or localhost origins in production —
        # both are unsafe with allow_credentials=True (see main.py CORS setup).
        for origin in settings.CORS_ORIGINS:
            normalized = origin.strip().lower()
            if normalized == "*":
                errors.append("CORS_ORIGINS must not contain '*' in production")
            elif "localhost" in normalized or "127.0.0.1" in normalized:
                errors.append(f"CORS_ORIGINS must not contain a localhost origin in production: {origin}")

    # Reject the well-known default secret and any secret shorter than 32 chars,
    # in every environment.
    if settings.JWT_SECRET_KEY == "change-me-in-production" or len(settings.JWT_SECRET_KEY) < 32:
        errors.append(f"JWT_SECRET_KEY is weak or too short ({len(settings.JWT_SECRET_KEY)} chars); use at least 32")

    if errors:
        for e in errors:
            log.error("SECURITY: %s", e)
        if settings.ENVIRONMENT == "production":
            sys.exit(f"Startup aborted due to {len(errors)} configuration error(s)")
