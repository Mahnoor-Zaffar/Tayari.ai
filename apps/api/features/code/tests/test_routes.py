"""Integration tests for the code execution API."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base, get_db
from features.auth.guard import CurrentUser, get_current_user
from features.code.seed_data import seed_problems
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


@pytest_asyncio.fixture
async def problem_db_override():
    """In-memory SQLite DB seeded with coding problems, wired into get_db."""
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await seed_problems(session)
        await session.commit()

        async def _get_db_override():
            yield session

        app.dependency_overrides[get_db] = _get_db_override
        yield
        app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


@pytest.mark.asyncio
async def test_list_problems(problem_db_override):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/code/problems")
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    problems = data["data"]["problems"]
    assert len(problems) >= 3
    two_sum = next((p for p in problems if p["slug"] == "two-sum"), None)
    assert two_sum is not None
    assert two_sum["difficulty"] == "medium"
    assert "test_cases" not in two_sum


@pytest.mark.asyncio
async def test_get_problem_hides_hidden_cases(problem_db_override):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/code/problems")
        problem_id = response.json()["data"]["problems"][0]["id"]
        detail = await client.get(f"/api/v1/code/problems/{problem_id}")
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["title"]
    assert isinstance(data["description"], str)
    assert data["total_test_count"] > data["hidden_test_count"]
    # Hidden cases must never be returned to the client.
    for tc in data["test_cases"]:
        assert tc["input"] is not None
    assert data["hidden_test_count"] > 0


@pytest.mark.asyncio
async def test_get_problem_not_found(problem_db_override):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/code/problems/00000000-0000-0000-0000-0000000000ff")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_with_problem_id(problem_db_override):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        problems = (await client.get("/api/v1/code/problems")).json()["data"]["problems"]
        problem_id = next(p for p in problems if p["slug"] == "reverse-string")["id"]
        source = (
            "import sys\n"
            "def solve(data):\n"
            "    return data[::-1]\n"
            "if __name__ == '__main__':\n"
            "    print(solve(sys.stdin.read().strip()))\n"
        )
        response = await client.post(
            "/api/v1/code/submit",
            json={
                "interview_id": "00000000-0000-0000-0000-000000000001",
                "language": "python",
                "source_code": source,
                "problem_id": problem_id,
            },
        )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["passed_count"] == data["total_count"]
    assert data["total_count"] > 0
    for tr in data["test_results"]:
        if tr["is_hidden"]:
            assert tr["actual_output"] is None
