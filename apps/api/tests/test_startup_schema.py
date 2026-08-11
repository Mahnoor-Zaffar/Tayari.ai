"""Regression tests for startup schema management (main.lifespan).

Schema creation via ``Base.metadata.create_all`` is a dev/test convenience only.
In production the schema is owned by Alembic, so the lifespan must NOT call
``create_all`` — otherwise the running schema can silently diverge from the
migration chain.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import main as main_module


class _FakeConn:
    def __init__(self, tracker: list[str]) -> None:
        self._tracker = tracker

    async def run_sync(self, fn) -> None:
        self._tracker.append("create_all")


def _fake_engine(tracker: list[str]) -> MagicMock:
    """Engine whose begin() records when create_all runs."""
    engine = MagicMock()

    @asynccontextmanager
    async def _begin():
        yield _FakeConn(tracker)

    engine.begin = _begin
    engine.dispose = AsyncMock()
    return engine


async def _drive_lifespan(monkeypatch, *, environment: str) -> list[str]:
    """Run the lifespan once with collaborators stubbed; return call tracker."""
    tracker: list[str] = []

    fake_settings = SimpleNamespace(
        SENTRY_DSN=None,
        ENVIRONMENT=environment,
        VERSION="test",
        is_development=environment in ("development", "test"),
        is_production=environment == "production",
    )

    monkeypatch.setattr(main_module, "settings", fake_settings)
    monkeypatch.setattr(main_module, "engine", _fake_engine(tracker))
    monkeypatch.setattr(main_module, "validate_prod_settings", lambda: None)

    # Scheduler is imported inside the lifespan from workers.scheduler.
    import workers.scheduler as scheduler_module

    monkeypatch.setattr(scheduler_module, "scheduler", MagicMock())

    # Skip DB-backed session restore (irrelevant to the schema guard).
    def _boom() -> None:
        raise RuntimeError("skip restore")

    monkeypatch.setattr(main_module, "async_session", _boom)

    async with main_module.lifespan(MagicMock()):
        pass

    return tracker


@pytest.mark.asyncio
async def test_create_all_skipped_in_production(monkeypatch):
    tracker = await _drive_lifespan(monkeypatch, environment="production")
    assert "create_all" not in tracker


@pytest.mark.asyncio
async def test_create_all_runs_in_development(monkeypatch):
    tracker = await _drive_lifespan(monkeypatch, environment="development")
    assert tracker.count("create_all") == 1
