from __future__ import annotations

import pytest

from core.rate_limit import InMemoryRateLimiter, RedisRateLimiter


class TestInMemoryRateLimiter:
    async def test_allows_up_to_max_then_blocks(self) -> None:
        limiter = InMemoryRateLimiter()
        for _ in range(3):
            assert await limiter.check("key", max_requests=3, window_seconds=60) is True
        assert await limiter.check("key", max_requests=3, window_seconds=60) is False

    async def test_window_expires_old_requests(self) -> None:
        limiter = InMemoryRateLimiter()
        for _ in range(3):
            assert await limiter.check("key", max_requests=3, window_seconds=60) is True
        assert await limiter.check("key", max_requests=3, window_seconds=0) is True

    async def test_keys_are_isolated(self) -> None:
        limiter = InMemoryRateLimiter()
        for _ in range(3):
            await limiter.check("a", max_requests=3, window_seconds=60)
        assert await limiter.check("b", max_requests=3, window_seconds=60) is True


class TestRedisRateLimiterFallback:
    async def test_falls_back_to_in_memory_when_redis_down(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def _boom(self) -> object:
            raise ConnectionError("redis unavailable")

        monkeypatch.setattr(RedisRateLimiter, "_get_redis", _boom)
        limiter = RedisRateLimiter(redis_url="redis://127.0.0.1:1/0")
        for _ in range(3):
            assert await limiter.check("key", max_requests=3, window_seconds=60) is True
        assert await limiter.check("key", max_requests=3, window_seconds=60) is False
