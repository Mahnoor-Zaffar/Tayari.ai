"""Tests for the analytics module.

Organised into three layers mirroring the module structure:
1. Repository integration tests
2. Service unit tests
3. API integration tests
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base
from features.analytics.dependencies import get_analytics_service
from features.analytics.repository import AnalyticsRepository
from features.analytics.schemas import AnalyticsResponse
from features.analytics.service import AnalyticsService
from features.auth.guard import CurrentUser, get_current_user
from main import app


@event.listens_for(Base.metadata, "before_create")
def _compile_jsonb_for_sqlite(target, connection, **kw):
    if connection.engine.dialect.name == "sqlite":
        for table in target.tables.values():
            for column in table.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()


def _ts(days_ago: int, **kwargs) -> datetime:
    return datetime.now(UTC) - timedelta(days=days_ago, **kwargs)


def _make_user() -> CurrentUser:
    return CurrentUser(
        id=uuid.uuid4(),
        email="alice@example.com",
        username="alice",
        display_name="Alice Smith",
        email_verified=True,
        is_active=True,
        roles=["user"],
        permissions=[],
    )


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(name="db_engine")
async def db_engine_fixture() -> AsyncGenerator:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(name="session")
async def session_fixture(db_engine) -> AsyncGenerator[AsyncSession]:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(name="repository")
async def repository_fixture(session: AsyncSession) -> AnalyticsRepository:
    return AnalyticsRepository(session)


@pytest_asyncio.fixture(name="seeded_session")
async def seeded_session_fixture(db_engine, session: AsyncSession) -> AsyncSession:
    """Seed a user with completed interviews for analytics."""
    from features.auth.models import User as UserORM
    from features.interview.models import Interview as InterviewORM

    user_id = uuid.uuid4()
    session.add(
        UserORM(
            id=user_id,
            email="alice@example.com",
            username="alice",
            display_name="Alice",
            password_hash="…",
        )
    )
    await session.flush()

    for days_ago, score in [(6, 85), (5, 72), (1, 90)]:
        iid = uuid.uuid4()
        session.add(
            InterviewORM(
                id=iid,
                user_id=user_id,
                type="coding",
                company="Acme",
                experience_level="mid",
                status="completed",
                completed_at=_ts(days_ago),
                created_at=_ts(days_ago + 1),
            )
        )
        await session.flush()

        from features.reports.models import Evaluation as EvaluationORM

        session.add(
            EvaluationORM(
                interview_id=iid,
                overall_score=score,
                hire_verdict="hire",
                status="completed",
            )
        )

    await session.commit()
    return session


@pytest_asyncio.fixture(name="seeded_user_id")
async def seeded_user_id_fixture(seeded_session: AsyncSession) -> uuid.UUID:
    from sqlalchemy import select

    from features.auth.models import User as UserORM

    return (await seeded_session.execute(select(UserORM.id).limit(1))).scalar_one()


@pytest_asyncio.fixture(name="seeded_repo")
async def seeded_repo_fixture(seeded_session: AsyncSession) -> AnalyticsRepository:
    return AnalyticsRepository(seeded_session)


# ═════════════════════════════════════════════════════════════════════════
# 1. Repository Integration Tests
# ═════════════════════════════════════════════════════════════════════════


class TestAnalyticsRepository:
    async def test_get_analytics_data_returns_empty_for_new_user(self, repository: AnalyticsRepository) -> None:
        data = await repository.get_analytics_data(uuid.uuid4())
        assert data == []

    async def test_get_analytics_data_returns_within_range(
        self, seeded_repo: AnalyticsRepository, seeded_user_id: uuid.UUID
    ) -> None:
        data = await seeded_repo.get_analytics_data(seeded_user_id)
        assert len(data) >= 3
        for row in data:
            assert "completed_at" in row
            assert "overall_score" in row


# ═════════════════════════════════════════════════════════════════════════
# 2. Service Unit Tests
# ═════════════════════════════════════════════════════════════════════════


class TestAnalyticsService:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_analytics_data = AsyncMock(
            return_value=[
                {"completed_at": _ts(0), "overall_score": 85.0},
                {"completed_at": _ts(1), "overall_score": 72.0},
                {"completed_at": _ts(2), "overall_score": 90.0},
            ]
        )
        return repo

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> AnalyticsService:
        return AnalyticsService(mock_repo)

    async def test_get_analytics_groups_correctly(self, service: AnalyticsService) -> None:
        result = await service.get_analytics(uuid.uuid4())
        assert isinstance(result, AnalyticsResponse)
        assert len(result.daily) >= 1
        assert len(result.weekly) >= 1
        assert len(result.monthly) >= 1

    async def test_get_analytics_with_no_data(self, mock_repo: MagicMock) -> None:
        mock_repo.get_analytics_data.return_value = []
        service = AnalyticsService(mock_repo)
        result = await service.get_analytics(uuid.uuid4())
        assert result.daily == []
        assert result.weekly == []
        assert result.monthly == []


# ═════════════════════════════════════════════════════════════════════════
# 3. API Integration Tests
# ═════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_service() -> MagicMock:
    svc = MagicMock()
    svc.get_analytics = AsyncMock(
        return_value=AnalyticsResponse(
            daily=[],
            weekly=[],
            monthly=[],
        )
    )
    return svc


@pytest.fixture
def current_user() -> CurrentUser:
    return _make_user()


@pytest.fixture
def client(
    mock_service: MagicMock,
    current_user: CurrentUser,
) -> AsyncClient:
    app.dependency_overrides[get_analytics_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: current_user
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test/api/v1")
    yield client
    app.dependency_overrides.clear()


class TestAnalyticsAPI:
    async def test_get_analytics_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/analytics")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "daily" in body["data"]
        assert "weekly" in body["data"]
        assert "monthly" in body["data"]

    async def test_get_analytics_requires_auth(self, mock_service: MagicMock) -> None:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_analytics_service] = lambda: mock_service
        transport = ASGITransport(app=app)
        unauth_client = AsyncClient(transport=transport, base_url="http://test/api/v1")
        response = await unauth_client.get("/analytics")
        assert response.status_code == 401
        app.dependency_overrides[get_current_user] = lambda: current_user
