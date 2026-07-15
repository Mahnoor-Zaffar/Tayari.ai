"""Integration tests for the code execution API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_list_languages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/code/languages")
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    langs = data["data"]["languages"]
    assert len(langs) >= 7
    assert any(lang["id"] == "python" for lang in langs)


@pytest.mark.asyncio
async def test_run_code_python():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/code/run",
            json={"language": "python", "source_code": 'print("hello from test")'},
        )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert data["data"]["stdout"].strip() == "hello from test"
    assert data["data"]["exit_code"] == 0


@pytest.mark.asyncio
async def test_run_code_unknown_language():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/code/run",
            json={"language": "brainfuck", "source_code": "..."},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_run_code_syntax_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/code/run",
            json={"language": "python", "source_code": "print(hello"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["exit_code"] != 0
