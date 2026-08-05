"""Integration tests for the code execution API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from features.auth.guard import CurrentUser, get_current_user
from main import app


@pytest.fixture(autouse=True)
def _auth_override():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id="00000000-0000-0000-0000-000000000001",
        email="test@test.com",
        username="testuser",
        display_name="Test User",
        email_verified=True,
        is_active=True,
        roles=["user"],
        permissions=["interview:read", "interview:write"],
    )
    yield
    app.dependency_overrides.clear()


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
async def test_run_code_requires_auth():
    app.dependency_overrides.clear()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/code/run",
                json={"language": "python", "source_code": 'print("hi")'},
            )
    finally:
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id="00000000-0000-0000-0000-000000000001",
            email="test@test.com",
            username="testuser",
            display_name="Test User",
            email_verified=True,
            is_active=True,
            roles=["user"],
            permissions=[],
        )
    assert response.status_code in (401, 403)


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
