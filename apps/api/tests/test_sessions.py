import pytest


@pytest.mark.asyncio
async def test_create_session_unauthorized(client):
    """POST /api/v1/sessions without auth token returns 401."""
    response = await client.post("/api/v1/sessions", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_session_bad_token(client):
    """POST /api/v1/sessions with invalid token returns 401."""
    response = await client.post(
        "/api/v1/sessions",
        json={},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_session_status_unauthorized(client):
    """GET /api/v1/sessions/{id} without auth returns 401."""
    response = await client.get("/api/v1/sessions/fake-id")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_evaluation_unauthorized(client):
    """GET /api/v1/evaluations/{id} without auth returns 401."""
    response = await client.get("/api/v1/evaluations/nonexistent-id")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_evaluations_unauthorized(client):
    """GET /api/v1/evaluations without auth returns 401."""
    response = await client.get("/api/v1/evaluations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_still_works(client):
    """Existing /health endpoint is unaffected by session tests."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
