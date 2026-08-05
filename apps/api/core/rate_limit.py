"""Sliding-window rate limiters.

``RedisRateLimiter`` shares state across app instances (multi-worker and
multi-replica deployments) via an auto-expiring Redis counter.  If Redis is
unreachable it degrades to an in-process window so brute-force protection
is never silently dropped on a single instance.

The module-level ``rate_limiter`` follows the same convention as the JWT
blacklist: local Redis URLs use the in-memory limiter (single-instance dev),
everything else uses Redis (shared production state).
"""

import logging
import time
from collections import defaultdict

from core.config import settings

log = logging.getLogger("app.rate_limit")


class InMemoryRateLimiter:
    """Sliding-window limiter backed by an in-process timestamp bucket."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def check(self, key: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds
        self._buckets[key] = [t for t in self._buckets[key] if t > window_start]
        if len(self._buckets[key]) >= max_requests:
            return False
        self._buckets[key].append(now)
        return True


class RedisRateLimiter:
    """Fixed-window limiter backed by Redis.

    Every call increments the ``tayari:rate:{key}`` counter and resets its
    TTL to the window on the first hit, so blocked attempts keep the key
    locked for the full window — a restart of the app cannot "forget" the
    backoff.  When Redis is unavailable the check falls back to an
    in-process window.
    """

    def __init__(
        self,
        redis_url: str = settings.REDIS_URL,
        *,
        fallback: InMemoryRateLimiter | None = None,
    ) -> None:
        self._redis_url = redis_url
        self._redis = None
        self._fallback = fallback or InMemoryRateLimiter()

    async def _get_redis(self):
        if self._redis is None:
            from redis.asyncio import from_url

            self._redis = await from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        return self._redis

    async def check(self, key: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        try:
            r = await self._get_redis()
            counter_key = f"tayari:rate:{key}"
            count = await r.incr(counter_key)
            if count == 1:
                await r.expire(counter_key, window_seconds)
            return int(count) <= max_requests
        except Exception as exc:
            log.warning("Redis rate limiter unavailable — using in-memory fallback: %s", exc)
            return await self._fallback.check(key, max_requests, window_seconds)


def _build_default() -> RedisRateLimiter | InMemoryRateLimiter:
    if settings.REDIS_URL and not settings.REDIS_URL.startswith("redis://localhost"):
        return RedisRateLimiter()
    return InMemoryRateLimiter()


rate_limiter: RedisRateLimiter | InMemoryRateLimiter = _build_default()
