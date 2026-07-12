import pytest


@pytest.mark.asyncio
async def test_ready_success(client, monkeypatch):
    """Returns 200 when database is reachable."""
    response = await client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert "dependencies" in body


@pytest.mark.asyncio
async def test_ready_has_database_key(client):
    response = await client.get("/ready")
    body = response.json()
    assert "database" in body["dependencies"]


@pytest.mark.asyncio
async def test_health_still_works(client):
    """Existing /health endpoint is unaffected."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
