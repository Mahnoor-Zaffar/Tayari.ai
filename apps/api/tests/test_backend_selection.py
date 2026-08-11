"""Regression tests for backend selection of JWT blacklist and rate limiter (T5).

Production must always use the Redis-backed implementations (shared, restart-safe
revocation and brute-force backoff), regardless of whether the configured Redis
hostname happens to be local. Non-production selects Redis only for a non-local
Redis URL, otherwise the in-memory implementation for tests / local dev.
"""

from __future__ import annotations

import core.rate_limit as rate_limit_module
import features.auth.dependencies as auth_deps
from core.rate_limit import InMemoryRateLimiter, RedisRateLimiter
from features.auth.jwt.jti_blacklist import MemoryBlacklist
from features.auth.jwt.redis_blacklist import RedisBlacklist

# ── Blacklist selection ──────────────────────────────────────────────────────


def test_blacklist_redis_in_production_even_with_local_url(monkeypatch):
    monkeypatch.setattr(auth_deps.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(auth_deps.settings, "REDIS_URL", "redis://localhost:6379/0")
    assert isinstance(auth_deps._select_blacklist(), RedisBlacklist)


def test_blacklist_redis_for_nonlocal_url_in_dev(monkeypatch):
    monkeypatch.setattr(auth_deps.settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(auth_deps.settings, "REDIS_URL", "redis://cache.internal:6379/0")
    assert isinstance(auth_deps._select_blacklist(), RedisBlacklist)


def test_blacklist_memory_for_local_url_in_dev(monkeypatch):
    monkeypatch.setattr(auth_deps.settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(auth_deps.settings, "REDIS_URL", "redis://localhost:6379/0")
    assert isinstance(auth_deps._select_blacklist(), MemoryBlacklist)


# ── Rate limiter selection ───────────────────────────────────────────────────


def test_rate_limiter_redis_in_production_even_with_local_url(monkeypatch):
    monkeypatch.setattr(rate_limit_module.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(rate_limit_module.settings, "REDIS_URL", "redis://localhost:6379/0")
    assert isinstance(rate_limit_module._build_default(), RedisRateLimiter)


def test_rate_limiter_memory_for_local_url_in_dev(monkeypatch):
    monkeypatch.setattr(rate_limit_module.settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(rate_limit_module.settings, "REDIS_URL", "redis://localhost:6379/0")
    assert isinstance(rate_limit_module._build_default(), InMemoryRateLimiter)
