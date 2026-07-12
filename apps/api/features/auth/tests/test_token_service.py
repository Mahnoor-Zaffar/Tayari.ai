"""Unit tests for JWT TokenService — create, verify, revoke, peek, and
token-family reuse detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from jose import jwt as jose_jwt  # noqa: N812 — import alias avoids shadowing 'jwt' module

from features.auth.exceptions import InvalidTokenError
from features.auth.jwt.config import JWTConfig
from features.auth.jwt.interfaces import TokenBlacklistProtocol
from features.auth.jwt.models import TokenPayload
from features.auth.jwt.service import TokenService

# ── Helpers ─────────────────────────────────────────────────────────────────


class InMemoryBlacklist(TokenBlacklistProtocol):
    """Thread-unsafe in-memory blacklist for tests."""

    def __init__(self) -> None:
        self._store: set[str] = set()

    async def add(self, jti: str, expires_at: datetime) -> None:
        self._store.add(jti)

    async def is_blacklisted(self, jti: str) -> bool:
        return jti in self._store


@pytest.fixture
def config() -> JWTConfig:
    return JWTConfig(SECRET_KEY="test-secret-key-that-is-long-enough-for-hs256")


@pytest.fixture
def blacklist() -> InMemoryBlacklist:
    return InMemoryBlacklist()


@pytest.fixture
def service(config: JWTConfig) -> TokenService:
    return TokenService(config)


@pytest.fixture
def service_with_blacklist(config: JWTConfig, blacklist: InMemoryBlacklist) -> TokenService:
    return TokenService(config, blacklist=blacklist)


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


# ── create_access_token ─────────────────────────────────────────────────────


class TestCreateAccessToken:
    def test_returns_jwt_string(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_contains_correct_claims(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id, roles=["admin"], permissions=["users:write"])
        decoded = _unverified_decode(token)

        assert decoded["sub"] == str(user_id)
        assert decoded["type"] == "access"
        assert decoded["roles"] == ["admin"]
        assert decoded["permissions"] == ["users:write"]
        assert decoded["iss"] == "tayari-ai"
        assert decoded["aud"] == "tayari-api"
        assert decoded["iat"] is not None
        assert decoded["exp"] is not None
        assert decoded["jti"] is not None
        assert "token_family" not in decoded

    def test_defaults_roles_and_permissions(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id)
        decoded = _unverified_decode(token)

        assert decoded["roles"] == []
        assert decoded["permissions"] == []

    def test_unique_jti_per_call(self, service: TokenService, user_id: UUID) -> None:
        t1 = _unverified_decode(service.create_access_token(user_id))
        t2 = _unverified_decode(service.create_access_token(user_id))

        assert t1["jti"] != t2["jti"]


# ── create_refresh_token ────────────────────────────────────────────────────


class TestCreateRefreshToken:
    def test_returns_jwt_string(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_refresh_token(user_id)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_contains_token_family(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_refresh_token(user_id)
        decoded = _unverified_decode(token)

        assert decoded["type"] == "refresh"
        assert isinstance(decoded.get("token_family"), str)
        assert len(decoded["token_family"]) > 0

    def test_uses_provided_token_family(self, service: TokenService, user_id: UUID) -> None:
        family = str(uuid4())
        token = service.create_refresh_token(user_id, token_family=family)
        decoded = _unverified_decode(token)

        assert decoded["token_family"] == family

    def test_different_tokens_have_different_families(self, service: TokenService, user_id: UUID) -> None:
        t1 = service.create_refresh_token(user_id)
        t2 = service.create_refresh_token(user_id)
        f1 = _unverified_decode(t1)["token_family"]
        f2 = _unverified_decode(t2)["token_family"]

        assert f1 != f2


# ── create_email_verification_token / create_password_reset_token ───────────


class TestCreateSpecialTokens:
    def test_email_verify_token_has_correct_type(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_email_verification_token(user_id)
        decoded = _unverified_decode(token)

        assert decoded["type"] == "email_verify"
        assert decoded["sub"] == str(user_id)

    def test_password_reset_token_has_correct_type(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_password_reset_token(user_id)
        decoded = _unverified_decode(token)

        assert decoded["type"] == "password_reset"
        assert decoded["sub"] == str(user_id)


# ── verify ──────────────────────────────────────────────────────────────────


class TestVerify:
    async def test_returns_token_payload_for_valid_access_token(
        self, service: TokenService, user_id: UUID
    ) -> None:
        token = service.create_access_token(user_id)
        payload = await service.verify(token, "access")

        assert isinstance(payload, TokenPayload)
        assert payload.sub == str(user_id)
        assert payload.type == "access"
        assert payload.roles == []
        assert payload.permissions == []

    async def test_returns_token_payload_for_valid_refresh_token(
        self, service: TokenService, user_id: UUID
    ) -> None:
        token = service.create_refresh_token(user_id)
        payload = await service.verify(token, "refresh")

        assert payload.sub == str(user_id)
        assert payload.type == "refresh"
        assert payload.token_family is not None

    async def test_raises_for_wrong_type(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id)

        with pytest.raises(InvalidTokenError, match="Expected token type 'refresh'"):
            await service.verify(token, "refresh")

    async def test_raises_for_expired_token(self, service: TokenService, user_id: UUID) -> None:
        config = JWTConfig(ACCESS_TOKEN_TTL=timedelta(seconds=-1))
        svc = TokenService(config)
        token = svc.create_access_token(user_id)

        with pytest.raises(InvalidTokenError, match="expired"):
            await svc.verify(token, "access")

    async def test_raises_for_tampered_token(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id) + "tampered"

        with pytest.raises(InvalidTokenError):
            await service.verify(token, "access")

    async def test_raises_for_nonsense_string(self, service: TokenService) -> None:
        with pytest.raises(InvalidTokenError):
            await service.verify("not.a.token", "access")

    async def test_raises_for_empty_string(self, service: TokenService) -> None:
        with pytest.raises(InvalidTokenError):
            await service.verify("", "access")

    async def test_raises_if_issuer_mismatch(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id)

        wrong_config = JWTConfig(SECRET_KEY="test-secret-key-that-is-long-enough-for-hs256", ISSUER="wrong-issuer")
        wrong_svc = TokenService(wrong_config)

        with pytest.raises(InvalidTokenError, match="issuer"):
            await wrong_svc.verify(token, "access")

    async def test_raises_if_audience_mismatch(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id)

        wrong_config = JWTConfig(
            SECRET_KEY="test-secret-key-that-is-long-enough-for-hs256", AUDIENCE="wrong-audience"
        )
        wrong_svc = TokenService(wrong_config)

        with pytest.raises(InvalidTokenError, match="audience"):
            await wrong_svc.verify(token, "access")

    async def test_raises_for_revoked_token(
        self, service_with_blacklist: TokenService, blacklist: InMemoryBlacklist, user_id: UUID
    ) -> None:
        token = service_with_blacklist.create_access_token(user_id)
        await service_with_blacklist.revoke(token)

        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(token, "access")

    async def test_raises_for_revoked_family(
        self, service_with_blacklist: TokenService, blacklist: InMemoryBlacklist, user_id: UUID
    ) -> None:
        family = str(uuid4())
        token1 = service_with_blacklist.create_refresh_token(user_id, token_family=family)
        token2 = service_with_blacklist.create_refresh_token(user_id, token_family=family)

        # Revoke the family
        await service_with_blacklist.revoke_family(family, datetime.now(UTC) + timedelta(hours=1))

        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(token1, "refresh")

        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(token2, "refresh")


# ── verify with blacklist ───────────────────────────────────────────────────


class TestVerifyWithBlacklist:
    async def test_passes_for_not_revoked_token(
        self, service_with_blacklist: TokenService, user_id: UUID
    ) -> None:
        token = service_with_blacklist.create_access_token(user_id)
        payload = await service_with_blacklist.verify(token, "access")

        assert payload.sub == str(user_id)

    async def test_passes_for_token_revoked_in_different_service(
        self, service_with_blacklist: TokenService, config: JWTConfig, user_id: UUID
    ) -> None:
        token = service_with_blacklist.create_access_token(user_id)
        _second_service = TokenService(config)
        payload = await _second_service.verify(token, "access")

        assert payload.sub == str(user_id)


# ── revoke ──────────────────────────────────────────────────────────────────


class TestRevoke:
    async def test_without_blacklist_is_noop(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id)
        # Should not raise
        await service.revoke(token)

        # Token should still be valid
        payload = await service.verify(token, "access")
        assert payload.sub == str(user_id)

    async def test_with_blacklist_adds_jti(
        self, service_with_blacklist: TokenService, blacklist: InMemoryBlacklist, user_id: UUID
    ) -> None:
        token = service_with_blacklist.create_access_token(user_id)
        decoded = _unverified_decode(token)

        await service_with_blacklist.revoke(token)

        assert await blacklist.is_blacklisted(decoded["jti"])


# ── revoke_family ───────────────────────────────────────────────────────────


class TestRevokeFamily:
    async def test_without_blacklist_is_noop(self, service: TokenService) -> None:
        await service.revoke_family("some-family", datetime.now(UTC))

    async def test_adds_family_prefix(
        self, service_with_blacklist: TokenService, blacklist: InMemoryBlacklist
    ) -> None:
        await service_with_blacklist.revoke_family("fam-1", datetime.now(UTC) + timedelta(hours=1))

        assert await blacklist.is_blacklisted("family:fam-1")


# ── peek ────────────────────────────────────────────────────────────────────


class TestPeek:
    def test_returns_claims_without_verification(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_access_token(user_id, roles=["user"])

        claims = service.peek(token)

        assert claims["sub"] == str(user_id)
        assert claims["type"] == "access"
        assert claims["roles"] == ["user"]

    def test_returns_empty_dict_for_garbage(self, service: TokenService) -> None:
        assert service.peek("not-a-token") == {}

    def test_returns_claims_even_for_expired_token(self, service: TokenService, user_id: UUID) -> None:
        config = JWTConfig(ACCESS_TOKEN_TTL=timedelta(days=-1))
        svc = TokenService(config)
        token = svc.create_access_token(user_id)

        claims = svc.peek(token)

        assert claims["sub"] == str(user_id)

    def test_returns_claims_even_for_wrong_signature(
        self, service: TokenService, config: JWTConfig, user_id: UUID
    ) -> None:
        svc_b = TokenService(JWTConfig(SECRET_KEY="different-secret-key-that-is-long-enough-for-hs256"))
        token = svc_b.create_access_token(user_id)

        claims = service.peek(token)

        assert claims["sub"] == str(user_id)

    def test_extracts_token_family(self, service: TokenService, user_id: UUID) -> None:
        token = service.create_refresh_token(user_id)

        claims = service.peek(token)

        assert "token_family" in claims
        assert isinstance(claims["token_family"], str)


# ── Reuse detection (integration-level scenario) ────────────────────────────


class TestReuseDetection:
    """Simulate a refresh-token rotation replay attack.

    TokenService.verify() rejects revoked tokens by jti.  The family‑level
    burn is triggered at the *route* layer (routes.py catches
    InvalidTokenError, calls peek() to extract the family, then calls
    revoke_family()).  These tests verify that both mechanisms work
    correctly when used together.
    """

    async def test_reused_token_is_rejected_by_jti(
        self, service_with_blacklist: TokenService, blacklist: InMemoryBlacklist, user_id: UUID
    ) -> None:
        original = service_with_blacklist.create_refresh_token(user_id)

        # First use — passes verify
        p1 = await service_with_blacklist.verify(original, "refresh")
        assert p1.sub == str(user_id)

        # Revoke by jti (simulates rotation)
        await service_with_blacklist.revoke(original)

        # Second use — rejected (jti blacklisted)
        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(original, "refresh")

    async def test_family_burn_invalidates_all_tokens_in_family(
        self, service_with_blacklist: TokenService, blacklist: InMemoryBlacklist, user_id: UUID
    ) -> None:
        """Verify that revoke_family() kills every token sharing the family."""
        family = str(uuid4())
        token_a = service_with_blacklist.create_refresh_token(user_id, token_family=family)
        token_b = service_with_blacklist.create_refresh_token(user_id, token_family=family)

        # Both tokens are valid
        assert (await service_with_blacklist.verify(token_a, "refresh")).sub == str(user_id)
        assert (await service_with_blacklist.verify(token_b, "refresh")).sub == str(user_id)

        # Burn the family (as the route handler would after detecting replay)
        await service_with_blacklist.revoke_family(family, datetime.now(UTC) + timedelta(hours=1))

        # Both are now dead
        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(token_a, "refresh")
        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(token_b, "refresh")

    async def test_full_replay_scenario(
        self, service_with_blacklist: TokenService, blacklist: InMemoryBlacklist, user_id: UUID
    ) -> None:
        """Simulate the complete route‑level replay‑detection flow."""
        original = service_with_blacklist.create_refresh_token(user_id)
        family = _unverified_decode(original)["token_family"]

        # 1. Normal rotation: verify + revoke old
        await service_with_blacklist.verify(original, "refresh")
        await service_with_blacklist.revoke(original)

        # 2. Replacement token issued
        replacement = service_with_blacklist.create_refresh_token(user_id, token_family=family)

        # 3. Attacker replays original → rejected by jti
        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(original, "refresh")

        # 4. Route handler detects replay, burns the family
        await service_with_blacklist.revoke_family(family, datetime.now(UTC) + timedelta(hours=1))

        # 5. Replacement is now also dead
        with pytest.raises(InvalidTokenError, match="revoked"):
            await service_with_blacklist.verify(replacement, "refresh")


# ── Token TTL boundary tests ────────────────────────────────────────────────


class TestTokenTTL:
    async def test_access_token_expired_when_past_ttl(self, user_id: UUID) -> None:
        """Token created with TTL in the past should be expired."""
        config = JWTConfig(ACCESS_TOKEN_TTL=timedelta(seconds=-1))
        svc = TokenService(config)
        token = svc.create_access_token(user_id)

        with pytest.raises(InvalidTokenError, match="expired"):
            await svc.verify(token, "access")

    async def test_token_just_before_expiry_is_valid(self, user_id: UUID) -> None:
        """Token created 14 minutes ago with 15-min TTL should still be valid."""
        config = JWTConfig(ACCESS_TOKEN_TTL=timedelta(minutes=15))
        svc = TokenService(config)

        # Manually create a token with iat=14min ago
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": now + timedelta(minutes=1),  # expires in 1 minute
            "iat": now - timedelta(minutes=14),  # issued 14 minutes ago
            "jti": str(uuid4()),
            "iss": config.ISSUER,
            "aud": config.AUDIENCE,
            "roles": [],
            "permissions": [],
        }
        token = jose_jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

        p = await svc.verify(token, "access")
        assert p.sub == str(user_id)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _unverified_decode(token: str) -> dict[str, Any]:
    """Decode JWT payload WITHOUT signature verification (for test assertions)."""
    return jose_jwt.get_unverified_claims(token)
