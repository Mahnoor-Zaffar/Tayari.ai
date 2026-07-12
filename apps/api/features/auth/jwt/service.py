from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt
from pydantic import ValidationError

from features.auth.exceptions import InvalidTokenError
from features.auth.jwt.config import JWTConfig
from features.auth.jwt.interfaces import TokenBlacklistProtocol
from features.auth.jwt.models import TokenPayload


class TokenService:
    """Cryptographically sound JWT creation and verification.

    * Creates typed tokens (access / refresh / email_verify / password_reset)
      with standard claims (sub, exp, iat, jti, iss, aud) plus custom claims
      (type, roles, permissions).
    * Verifies signature, expiry, issuer, audience, and token type.
    * Supports optional revocation via a ``TokenBlacklistProtocol`` backend.
    * Designed for OAuth2 extension: separate issuer/audience, asymmetric
      algorithm support, and claim structure compatible with JWKS.
    """

    def __init__(
        self,
        config: JWTConfig,
        blacklist: TokenBlacklistProtocol | None = None,
    ) -> None:
        self._config = config
        self._blacklist = blacklist

    # ── Public API ────────────────────────────────────────────────────────

    def create_access_token(
        self,
        user_id: UUID,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> str:
        return self._encode(
            sub=str(user_id),
            token_type="access",
            ttl=self._config.ACCESS_TOKEN_TTL,
            extra={"roles": roles or [], "permissions": permissions or []},
        )

    def create_refresh_token(self, user_id: UUID, token_family: str | None = None) -> str:
        extra = {"token_family": token_family or str(uuid4())}
        return self._encode(
            sub=str(user_id),
            token_type="refresh",
            ttl=self._config.REFRESH_TOKEN_TTL,
            extra=extra,
        )

    def create_email_verification_token(self, user_id: UUID) -> str:
        return self._encode(
            sub=str(user_id),
            token_type="email_verify",
            ttl=self._config.EMAIL_VERIFY_TTL,
        )

    def create_password_reset_token(self, user_id: UUID) -> str:
        return self._encode(
            sub=str(user_id),
            token_type="password_reset",
            ttl=self._config.PASSWORD_RESET_TTL,
        )

    async def verify(self, token: str, expected_type: str) -> TokenPayload:
        """Decode, validate, and return a typed token payload.

        Steps performed in order:
        1. Signature validation (rejects tampered tokens).
        2. Expiry check (``exp`` claim against current time).
        3. Required claims presence (sub, type, exp, iat, jti, iss, aud).
        4. Issuer (``iss``) and audience (``aud``) match.
        5. Token ``type`` matches *expected_type*.
        6. Blacklist lookup (if a backend is configured).
        """
        try:
            data = jwt.decode(
                token,
                self._verifying_key,
                algorithms=[self._config.ALGORITHM],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require": ["sub", "type", "exp", "iat", "jti", "iss", "aud"],
                },
                audience=self._config.AUDIENCE,
                issuer=self._config.ISSUER,
            )
        except JWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        if data.get("type") != expected_type:
            raise InvalidTokenError(f"Expected token type '{expected_type}', got '{data.get('type')}'")

        if self._blacklist is not None:
            jti = data.get("jti", "")
            if await self._blacklist.is_blacklisted(jti):
                raise InvalidTokenError("Token has been revoked")
            family = data.get("token_family", "")
            if family and await self._blacklist.is_blacklisted(f"family:{family}"):
                raise InvalidTokenError("Token family has been revoked")

        try:
            return TokenPayload(**data)
        except ValidationError as exc:
            raise InvalidTokenError(f"Token payload validation failed: {exc}") from exc

    async def revoke(self, token: str) -> None:
        """Revoke a token so that subsequent ``verify()`` calls reject it.

        Requires a ``TokenBlacklistProtocol`` backend to be configured.
        """
        if self._blacklist is None:
            return

        data = jwt.decode(
            token,
            self._verifying_key,
            algorithms=[self._config.ALGORITHM],
            options={"verify_exp": True, "verify_aud": False, "verify_iss": False},
        )
        jti = data.get("jti", "")
        exp_ts = data.get("exp")
        expires_at = datetime.fromtimestamp(exp_ts, tz=UTC) if exp_ts else datetime.now(UTC)
        await self._blacklist.add(jti, expires_at)

    def peek(self, token: str) -> dict:
        """Decode token *without* cryptographic verification.

        The caller **must not** trust the returned claims for access-control
        decisions — only for logging, telemetry, or extracting the
        ``token_family`` after a revocation event.
        """
        try:
            return jwt.get_unverified_claims(token)
        except JWTError:
            return {}

    async def revoke_family(self, token_family: str, expires_at: datetime) -> None:
        """Revoke every token bearing *token_family* so future ``verify()``
        calls reject them.

        This is the second line of defence against token theft: when a
        rotated refresh token is reused, the entire family is burned so
        that the stolen replacement token is also invalidated.
        """
        if self._blacklist is None:
            return
        await self._blacklist.add(f"family:{token_family}", expires_at)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _encode(
        self,
        sub: str,
        token_type: str,
        ttl: timedelta,
        extra: dict | None = None,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": sub,
            "type": token_type,
            "exp": now + ttl,
            "iat": now,
            "jti": str(uuid4()),
            "iss": self._config.ISSUER,
            "aud": self._config.AUDIENCE,
            **(extra or {}),
        }
        return jwt.encode(payload, self._signing_key, algorithm=self._config.ALGORITHM)

    @property
    def _signing_key(self) -> str:
        return self._config.SECRET_KEY

    @property
    def _verifying_key(self) -> str:
        return self._config.PUBLIC_KEY or self._config.SECRET_KEY
