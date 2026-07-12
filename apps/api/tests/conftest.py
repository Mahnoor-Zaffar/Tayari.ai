import pytest


@pytest.fixture
def client():
    from httpx import ASGITransport, AsyncClient

    from main import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
