"""Regression tests for production configuration validation (core/secrets.py).

These lock in two behaviours:
  - A strong JWT secret passes validation (previously a logic bug rejected
    every secret because it required the literal substring "SECRET_KEY").
  - The default/short secret and unsafe production CORS origins are rejected.
"""

from __future__ import annotations

import pytest

import core.secrets as secrets_module
from core.config import Settings


def _run(monkeypatch, **overrides) -> None:
    """Invoke validate_prod_settings() with a patched settings object."""
    base = {
        "ENVIRONMENT": "production",
        "JWT_SECRET_KEY": "a" * 40,
        "JWT_ALGORITHM": "RS256",
        "CORS_ORIGINS": ["https://app.tayari.ai"],
        "RESEND_API_KEY": "re_test",
        "DATABASE_URL": "postgresql+asyncpg://user:pw@db.example.com:5432/tayari",
    }
    base.update(overrides)
    monkeypatch.setattr(secrets_module, "settings", Settings(**base))
    secrets_module.validate_prod_settings()


def test_strong_secret_passes(monkeypatch):
    # Should not raise SystemExit.
    _run(monkeypatch, JWT_SECRET_KEY="x" * 64)


def test_default_secret_rejected(monkeypatch):
    with pytest.raises(SystemExit):
        _run(monkeypatch, JWT_SECRET_KEY="change-me-in-production")


def test_short_secret_rejected(monkeypatch):
    with pytest.raises(SystemExit):
        _run(monkeypatch, JWT_SECRET_KEY="tooshort")


def test_wildcard_cors_rejected_in_prod(monkeypatch):
    with pytest.raises(SystemExit):
        _run(monkeypatch, CORS_ORIGINS=["*"])


def test_localhost_cors_rejected_in_prod(monkeypatch):
    with pytest.raises(SystemExit):
        _run(monkeypatch, CORS_ORIGINS=["http://localhost:3000"])


def test_https_cors_allowed_in_prod(monkeypatch):
    _run(monkeypatch, CORS_ORIGINS=["https://app.tayari.ai", "https://www.tayari.ai"])


def test_localhost_cors_allowed_in_dev(monkeypatch):
    # In development the same origin only logs; it must not exit.
    _run(monkeypatch, ENVIRONMENT="development", CORS_ORIGINS=["http://localhost:3000"], JWT_SECRET_KEY="y" * 40)
