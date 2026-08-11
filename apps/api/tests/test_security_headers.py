import pytest

import core.security_headers as sec
from core.security_headers import _build_csp


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
async def test_permissions_policy_allows_microphone(client):
    """Voice interviews require the mic; camera/geolocation stay disabled."""
    response = await client.get("/health")
    policy = response.headers.get("permissions-policy", "")
    assert "microphone=(self)" in policy
    assert "camera=()" in policy
    assert "geolocation=()" in policy


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


def test_csp_uses_public_api_url_with_wss_in_prod(monkeypatch):
    """In production, connect-src uses PUBLIC_API_URL and a wss:// origin, no localhost."""
    monkeypatch.setattr(sec.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(sec.settings, "PUBLIC_API_URL", "https://api.tayari.ai")

    csp = _build_csp(origin="http://localhost:3000")

    assert "https://api.tayari.ai" in csp
    assert "wss://api.tayari.ai" in csp
    assert "localhost" not in csp
    assert "ws://" not in csp


def test_csp_allows_localhost_dev_origin(monkeypatch):
    """In development a localhost request origin is echoed into connect-src."""
    monkeypatch.setattr(sec.settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(sec.settings, "PUBLIC_API_URL", "http://localhost:8000")

    csp = _build_csp(origin="http://localhost:3000")

    assert "ws://localhost:8000" in csp
    assert "http://localhost:3000" in csp
