import pytest


@pytest.mark.asyncio
async def test_security_headers_present(client):
    response = await client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "0"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "permissions-policy" in response.headers
    assert "content-security-policy" in response.headers


@pytest.mark.asyncio
async def test_server_header_stripped(client):
    response = await client.get("/health")
    assert "server" not in response.headers
    assert "x-powered-by" not in response.headers


@pytest.mark.asyncio
async def test_csp_contains_default_src(client):
    response = await client.get("/health")
    csp = response.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp


@pytest.mark.asyncio
async def test_hsts_not_set_in_dev(client):
    """HSTS should only be set in production environment."""
    response = await client.get("/health")
    hsts = response.headers.get("strict-transport-security", "")
    assert hsts == ""
