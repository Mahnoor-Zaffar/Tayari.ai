"""Covers remaining uncovered lines to push coverage past 90%.

Targets:
- core/errors.py: AppError with details, AppError with request_id,
  ValidationError with details, RateLimitedError, DatabaseError, InternalError
- features/auth/jwt/service.py: TokenPayload validation error path
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from jose import jwt as jose_jwt

from core.errors import (
    AppError,
    ConflictError,
    DatabaseError,
    ErrorCode,
    InternalError,
    RateLimitedError,
    ValidationError,
    success_response,
)

# ── core.errors ─────────────────────────────────────────────────────────────


class TestAppError:
    def test_with_details(self) -> None:
        err = AppError("TEST", "msg", details=[{"field": "email", "msg": "invalid"}])
        payload = err.detail
        assert payload["error"]["details"] == [{"field": "email", "msg": "invalid"}]

    def test_with_request_id(self) -> None:
        err = AppError("TEST", "msg", request_id="abc-123")
        payload = err.detail
        assert payload["request_id"] == "abc-123"

    def test_validation_error_with_details(self) -> None:
        err = ValidationError(details=[{"loc": ["body", "email"], "msg": "invalid"}])
        assert err.status_code == 422
        assert err.detail["error"]["details"] is not None


class TestSpecificErrors:
    def test_rate_limited_error(self) -> None:
        err = RateLimitedError("Too fast")
        assert err.status_code == 429
        assert err.detail["error"]["code"] == ErrorCode.RATE_LIMITED

    def test_database_error(self) -> None:
        err = DatabaseError("DB down")
        assert err.status_code == 500
        assert err.detail["error"]["code"] == ErrorCode.DATABASE_ERROR

    def test_internal_error(self) -> None:
        err = InternalError("Boom")
        assert err.status_code == 500
        assert err.detail["error"]["code"] == ErrorCode.INTERNAL_ERROR

    def test_conflict_error(self) -> None:
        err = ConflictError("Already exists")
        assert err.status_code == 409
        assert err.detail["error"]["code"] == ErrorCode.CONFLICT

    def test_success_response(self) -> None:
        result = success_response({"key": "value"})
        assert result["success"] is True
        assert result["data"] == {"key": "value"}


# ── features/auth/jwt/service : TokenPayload validation error ───────────────


class TestTokenPayloadValidationError:
    """Trigger the ValidationError path inside TokenService.verify()."""

    @pytest.fixture
    def service(self):
        from features.auth.jwt.config import JWTConfig
        from features.auth.jwt.service import TokenService

        return TokenService(JWTConfig(SECRET_KEY="test-secret-key-that-is-long-enough-for-hs256"))

    async def test_rejects_payload_missing_sub(self, service) -> None:
        """A token missing ``sub`` should fail TokenPayload validation."""
        config = service._config
        payload = {
            "type": "access",
            "exp": datetime.now(UTC),
            "iat": datetime.now(UTC),
            "jti": str(uuid4()),
            "iss": config.ISSUER,
            "aud": config.AUDIENCE,
        }
        token = jose_jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

        from features.auth.exceptions import InvalidTokenError

        with pytest.raises(InvalidTokenError, match="validation"):
            await service.verify(token, "access")
