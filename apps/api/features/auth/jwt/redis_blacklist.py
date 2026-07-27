"""Redis-backed JWT blacklist with automatic TTL-based key expiry.

Replaces ``MemoryBlacklist`` in production deployments.  Each revoked JWT
``jti`` is stored as a Redis key with a TTL matching the token's remaining
lifetime, so expired revocations are cleaned up automatically.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from core.config import settings
from features.auth.jwt.interfaces import TokenBlacklistProtocol

log = logging.getLogger("app.auth.jwt.blacklist")

_REDIS_URL = settings.REDIS_URL

# Short TTL for entries without an explicit expiry (safety net).
_FALLBACK_TTL_SECONDS = 86400  # 24 hours


class RedisBlacklist(TokenBlacklistProtocol):
    """Revoked-token store backed by Redis.

    Keys are stored as ``tayari:blacklist:{jti}`` with a TTL equal to the
    token's remaining lifetime.  Family-level revocations use the key
    ``tayari:blacklist:family:{token_family}``.
    """

    def __init__(self, redis_url: str = _REDIS_URL) -> None:
        self._redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            from redis.asyncio import from_url

            self._redis = await from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            log.info("Connected to Redis for JWT blacklist")
        return self._redis

    async def add(self, jti: str, expires_at: datetime) -> None:
        r = await self._get_redis()
        ttl = max(1, int((expires_at - datetime.now(UTC)).total_seconds()))
        key = self._key(jti)
        await r.set(key, "1", ex=ttl)
        log.debug("Blacklisted jti=%s (ttl=%ds)", jti, ttl)

    async def is_blacklisted(self, jti: str) -> bool:
        try:
            r = await self._get_redis()
            return await r.exists(self._key(jti)) == 1
        except Exception as exc:
            log.error("Redis blacklist check failed for jti=%s: %s", jti, exc)
            return False

    @staticmethod
    def _key(jti: str) -> str:
        return f"tayari:blacklist:{jti}"
