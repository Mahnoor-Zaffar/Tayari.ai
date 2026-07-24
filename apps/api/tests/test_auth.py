import pytest


@pytest.mark.asyncio
async def test_login_invalid_email(client):
    """POST /api/v1/auth/login with invalid email returns 422."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "somepass"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_password(client):
    """POST /api/v1/auth/login without password returns 422."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_payload(client):
    """POST /api/v1/auth/register with empty body returns 422."""
    response = await client.post("/api/v1/auth/signup", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    """POST /api/v1/auth/signup with invalid email returns 422."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "bad-email",
            "username": "testuser",
            "display_name": "Test User",
            "password": "password123",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    """POST /api/v1/auth/signup with short password returns 422."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "display_name": "Test User",
            "password": "short",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_username(client):
    """POST /api/v1/auth/signup with short username returns 422."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "username": "ab",
            "display_name": "Test User",
            "password": "password123",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_user_not_found(client):
    """POST /api/v1/auth/login with non-existent user returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@tayari.ai", "password": "password123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_still_returns_ok(client):
    """Existing /health endpoint is unaffected by auth tests."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
