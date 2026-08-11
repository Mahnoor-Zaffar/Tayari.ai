"""Regression tests for the sandbox production fail-safe (T4).

The subprocess fallback provides no isolation. In production, if the Docker
sandbox is unavailable, ``Sandbox.run`` must refuse rather than silently execute
untrusted code unsandboxed. In development the fallback remains available.
"""

from __future__ import annotations

import pytest

import judge.sandbox as sandbox_module
from core.errors import AppError
from judge.sandbox import Sandbox


@pytest.mark.asyncio
async def test_run_refuses_without_docker_in_production(monkeypatch):
    monkeypatch.setattr(Sandbox, "USE_DOCKER", False)
    monkeypatch.setattr(sandbox_module.settings, "ENVIRONMENT", "production")

    called = False

    async def _should_not_run(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(Sandbox, "_run_subprocess", classmethod(lambda cls, *a, **k: _should_not_run()))

    with pytest.raises(AppError) as exc_info:
        await Sandbox.run("print('hi')", "python")

    assert exc_info.value.status_code == 500
    assert called is False


@pytest.mark.asyncio
async def test_run_falls_back_to_subprocess_in_development(monkeypatch):
    monkeypatch.setattr(Sandbox, "USE_DOCKER", False)
    monkeypatch.setattr(sandbox_module.settings, "ENVIRONMENT", "development")

    sentinel = object()

    async def _fake_subprocess(*args, **kwargs):
        return sentinel

    monkeypatch.setattr(Sandbox, "_run_subprocess", classmethod(lambda cls, *a, **k: _fake_subprocess()))

    result = await Sandbox.run("print('hi')", "python")
    assert result is sentinel


@pytest.mark.asyncio
async def test_run_uses_docker_when_available(monkeypatch):
    monkeypatch.setattr(Sandbox, "USE_DOCKER", True)
    monkeypatch.setattr(sandbox_module.settings, "ENVIRONMENT", "production")

    sentinel = object()

    async def _fake_docker(*args, **kwargs):
        return sentinel

    monkeypatch.setattr(Sandbox, "_run_docker", classmethod(lambda cls, *a, **k: _fake_docker()))

    result = await Sandbox.run("print('hi')", "python")
    assert result is sentinel
