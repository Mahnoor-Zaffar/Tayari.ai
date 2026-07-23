"""Tests for the dashboard module.

Organised into three layers mirroring the module structure:

1. ``TestDashboardRepository``  — integration tests against SQLite
2. ``TestDashboardService``     — unit tests with mocked repository
3. ``TestDashboardAPI``         — API-level tests with mocked services + auth
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
from features.auth.guard import CurrentUser, get_current_user
from features.dashboard.dependencies import get_dashboard_service
from features.dashboard.repository import DashboardRepository
from features.dashboard.schemas import (
    DashboardResponse,
    DashboardStats,
    LatestReport,
    RecentInterview,
    SubscriptionInfo,
    UserProfile,
)
from features.dashboard.service import DashboardService
from main import app

# Note: time-series analytics tests moved to ``features/analytics/tests/test_analytics.py``

# ── SQLite JSONB compatibility ──────────────────────────────────────────────


@event.listens_for(Base.metadata, "before_create")
def _compile_jsonb_for_sqlite(target, connection, **kw):
    """Swap PostgreSQL JSONB for generic JSON when running against SQLite."""
    if connection.engine.dialect.name == "sqlite":
        for table in target.tables.values():
            for column in table.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()


# ── Helpers ─────────────────────────────────────────────────────────────────


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


def _ts(days_ago: int, **kwargs) -> datetime:
    """Return a UTC datetime offset from now."""
    return datetime.now(UTC) - timedelta(days=days_ago, **kwargs)


# ═════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════════════


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
async def repository_fixture(session: AsyncSession) -> DashboardRepository:
    return DashboardRepository(session)


@pytest_asyncio.fixture(name="session_with_data")
async def session_with_data_fixture(db_engine, repository: DashboardRepository, session: AsyncSession) -> AsyncSession:
    """Seed the database with a user, interviews, evaluations, and a subscription.

    Data timeline (relative to now):
      - Completed 6 days ago (score 85)
      - Completed 5 days ago (score 72)
      - Completed 1 day ago  (score 90)   — latest report
      - Completed today                    — contributes to streak
      - In-progress                        — active
      - Pending                            — active
      - Soft-deleted                       — excluded from counts
    """
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

    # Interviews
    _add_interview(session, user_id, "completed", _ts(6), _ts(7))
    _add_interview(session, user_id, "completed", _ts(5), _ts(6))
    _add_interview(session, user_id, "completed", _ts(1), _ts(2))
    _add_interview(session, user_id, "completed", _ts(0), _ts(0, hours=2))
    _add_interview(session, user_id, "active", None, _ts(0, hours=1))
    _add_interview(session, user_id, "pending", None, _ts(0, hours=1))

    # Soft-deleted interview (should be excluded)
    from sqlalchemy import select

    del_id = uuid.uuid4()
    stmt = InterviewORM.__table__.insert().values(
        id=del_id,
        user_id=user_id,
        type="coding",
        company="Acme",
        experience_level="mid",
        status="completed",
        completed_at=_ts(3),
        created_at=_ts(4),
        deleted_at=datetime.now(UTC),
    )
    await session.execute(stmt)

    # Evaluations for completed interviews
    await session.flush()

    completed_ids = (
        (
            await session.execute(
                select(InterviewORM.id).where(
                    InterviewORM.user_id == user_id,
                    InterviewORM.status == "completed",
                    InterviewORM.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )

    scores = [85, 72, 90, None]  # 4th has no score (in progress turned completed w/o eval)
    for idx, iid in enumerate(completed_ids):
        score = scores[idx] if idx < len(scores) else None
        from features.reports.models import Evaluation as EvaluationORM

        session.add(
            EvaluationORM(
                interview_id=iid,
                overall_score=score,
                hire_verdict="strong_hire" if score and score >= 85 else "hire" if score else None,
                status="completed",
                created_at=_ts(6 - idx),
            )
        )

    # Subscription
    from features.billing.models import Subscription as SubscriptionORM

    session.add(
        SubscriptionORM(
            user_id=user_id,
            stripe_subscription_id="sub_123",
            status="active",
            plan="pro",
            current_period_start=_ts(30),
            current_period_end=_ts(335),
        )
    )

    await session.commit()
    return session


def _add_interview(
    session: AsyncSession,
    user_id: uuid.UUID,
    status: str,
    completed_at: datetime | None,
    created_at: datetime,
) -> None:
    from features.interview.models import Interview as InterviewORM

    session.add(
        InterviewORM(
            id=uuid.uuid4(),
            user_id=user_id,
            type="coding",
            company="Acme",
            experience_level="mid",
            status=status,
            completed_at=completed_at,
            created_at=created_at,
        )
    )


@pytest_asyncio.fixture(name="seeded_repo")
async def seeded_repo_fixture(session_with_data: AsyncSession) -> DashboardRepository:
    return DashboardRepository(session_with_data)


@pytest_asyncio.fixture(name="seeded_user_id")
async def seeded_user_id_fixture(session_with_data: AsyncSession) -> uuid.UUID:
    from sqlalchemy import select

    from features.auth.models import User as UserORM

    return (await session_with_data.execute(select(UserORM.id).limit(1))).scalar_one()


# ═════════════════════════════════════════════════════════════════════════════
# 1. Repository Integration Tests
# ═════════════════════════════════════════════════════════════════════════════


class TestDashboardRepository:
    async def test_get_stats_returns_zeros_for_new_user(self, repository: DashboardRepository) -> None:
        stats = await repository.get_stats(uuid.uuid4())
        assert stats["total_interviews"] == 0
        assert stats["completed_interviews"] == 0
        assert stats["active_interviews"] == 0
        assert stats["average_score"] is None

    async def test_get_stats_aggregates_correctly(
        self, seeded_repo: DashboardRepository, seeded_user_id: uuid.UUID
    ) -> None:
        stats = await seeded_repo.get_stats(seeded_user_id)
        assert stats["total_interviews"] == 6  # 4 completed + 1 active + 1 pending (soft-deleted excluded)
        assert stats["completed_interviews"] == 4
        assert stats["active_interviews"] == 2  # 1 active + 1 pending
        assert stats["average_score"] is not None

    async def test_get_streak_returns_zero_for_no_activity(self, repository: DashboardRepository) -> None:
        streak = await repository.get_streak(uuid.uuid4())
        assert streak == 0

    async def test_get_streak_returns_consecutive_days(
        self, seeded_repo: DashboardRepository, seeded_user_id: uuid.UUID
    ) -> None:
        streak = await seeded_repo.get_streak(seeded_user_id)
        assert streak >= 1

    async def test_get_streak_breaks_on_gap(self, repository: DashboardRepository) -> None:
        """Create interviews with a gap — streak should be 0 (not today/yesterday)."""
        from features.auth.models import User as UserORM
        from features.interview.models import Interview as InterviewORM

        user_id = uuid.uuid4()
        repository._session.add(
            UserORM(id=user_id, email="bob@example.com", username="bob", display_name="Bob", password_hash="…")
        )
        await repository._session.flush()

        # Completed 3 days ago — gap means no streak
        repository._session.add(
            InterviewORM(
                id=uuid.uuid4(),
                user_id=user_id,
                type="behavioral",
                company="Corp",
                experience_level="senior",
                status="completed",
                completed_at=_ts(3),
                created_at=_ts(4),
            )
        )
        await repository._session.flush()

        streak = await repository.get_streak(user_id)
        assert streak == 0

    async def test_get_latest_report_returns_most_recent(
        self, seeded_repo: DashboardRepository, seeded_user_id: uuid.UUID
    ) -> None:
        report = await seeded_repo.get_latest_report(seeded_user_id)
        assert report is not None
        assert report["interview_id"] is not None
        # The most recently created evaluation has score=None,
        # so hire_verdict should be None for that record.
        assert report["hire_verdict"] is None

    async def test_get_latest_report_returns_none_when_no_evaluations(self, repository: DashboardRepository) -> None:
        report = await repository.get_latest_report(uuid.uuid4())
        assert report is None

    async def test_get_subscription_returns_active(
        self, seeded_repo: DashboardRepository, seeded_user_id: uuid.UUID
    ) -> None:
        sub = await seeded_repo.get_subscription(seeded_user_id)
        assert sub is not None
        assert sub["plan"] == "pro"
        assert sub["status"] == "active"

    async def test_get_subscription_returns_none_when_missing(self, repository: DashboardRepository) -> None:
        sub = await repository.get_subscription(uuid.uuid4())
        assert sub is None

    async def test_get_recent_interviews_returns_ordered(
        self, seeded_repo: DashboardRepository, seeded_user_id: uuid.UUID
    ) -> None:
        interviews = await seeded_repo.get_recent_interviews(seeded_user_id)
        assert len(interviews) >= 3
        # Most recent first
        for i in range(len(interviews) - 1):
            assert interviews[i]["created_at"] >= interviews[i + 1]["created_at"]

    async def test_get_recent_interviews_respects_limit(
        self, seeded_repo: DashboardRepository, seeded_user_id: uuid.UUID
    ) -> None:
        interviews = await seeded_repo.get_recent_interviews(seeded_user_id, limit=2)
        assert len(interviews) <= 2


# ═════════════════════════════════════════════════════════════════════════════
# 2. Service Unit Tests
# ═════════════════════════════════════════════════════════════════════════════


class TestDashboardService:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_user_profile = AsyncMock(
            return_value={
                "id": uuid.uuid4(),
                "email": "alice@example.com",
                "username": "alice",
                "display_name": "Alice Smith",
                "email_verified": True,
                "created_at": _ts(365),
            }
        )
        repo.get_stats = AsyncMock(
            return_value={
                "total_interviews": 10,
                "completed_interviews": 7,
                "active_interviews": 2,
                "average_score": 81.5,
            }
        )
        repo.get_streak = AsyncMock(return_value=3)
        repo.get_latest_report = AsyncMock(
            return_value={
                "interview_id": uuid.uuid4(),
                "overall_score": 92.0,
                "hire_verdict": "strong_hire",
                "created_at": _ts(0),
            }
        )
        repo.get_subscription = AsyncMock(
            return_value={
                "plan": "pro",
                "status": "active",
                "current_period_end": _ts(-335),
            }
        )
        repo.get_recent_interviews = AsyncMock(
            return_value=[
                {
                    "id": uuid.uuid4(),
                    "type": "coding",
                    "company": "Acme",
                    "status": "completed",
                    "overall_score": 85.0,
                    "completed_at": _ts(0),
                    "created_at": _ts(1),
                }
            ]
        )
        return repo

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> DashboardService:
        return DashboardService(mock_repo)

    async def test_get_dashboard_returns_full_response(self, service: DashboardService) -> None:
        result = await service.get_dashboard(uuid.uuid4())

        assert isinstance(result, DashboardResponse)
        assert result.user.email == "alice@example.com"
        assert result.stats.total_interviews == 10
        assert result.stats.completed_interviews == 7
        assert result.stats.current_streak == 3
        assert result.stats.average_score == 81.5
        assert result.subscription is not None
        assert result.subscription.plan == "pro"
        assert result.latest_report is not None
        assert result.latest_report.hire_verdict == "strong_hire"

    async def test_get_dashboard_handles_missing_subscription_and_report(self, mock_repo: MagicMock) -> None:
        mock_repo.get_latest_report.return_value = None
        mock_repo.get_subscription.return_value = None
        service = DashboardService(mock_repo)

        result = await service.get_dashboard(uuid.uuid4())

        assert result.subscription is None
        assert result.latest_report is None
        assert result.stats.total_interviews == 10

    async def test_get_recent_interviews_returns_list(self, service: DashboardService) -> None:
        result = await service.get_recent_interviews(uuid.uuid4())
        assert len(result) == 1
        assert isinstance(result[0], RecentInterview)
        assert result[0].company == "Acme"


# ═════════════════════════════════════════════════════════════════════════════
# 3. API Integration Tests
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_dashboard_service() -> MagicMock:
    svc = MagicMock()
    svc.get_dashboard = AsyncMock(
        return_value=DashboardResponse(
            user=UserProfile(
                id=uuid.uuid4(),
                email="alice@example.com",
                username="alice",
                display_name="Alice Smith",
                email_verified=True,
                created_at=_ts(365),
            ),
            stats=DashboardStats(
                total_interviews=10,
                completed_interviews=7,
                active_interviews=2,
                average_score=81.5,
                current_streak=3,
                credits_remaining=100,
            ),
            subscription=SubscriptionInfo(plan="pro", status="active", current_period_end=_ts(-335)),
            latest_report=LatestReport(
                interview_id=uuid.uuid4(), overall_score=92.0, hire_verdict="strong_hire", created_at=_ts(0)
            ),
        )
    )
    svc.get_recent_interviews = AsyncMock(
        return_value=[
            RecentInterview(
                id=uuid.uuid4(),
                type="coding",
                company="Acme",
                status="completed",
                overall_score=85.0,
                completed_at=_ts(0),
                created_at=_ts(1),
            )
        ]
    )
    return svc


@pytest.fixture
def current_user() -> CurrentUser:
    return _make_user()


@pytest.fixture
def client(
    mock_dashboard_service: MagicMock,
    current_user: CurrentUser,
) -> AsyncClient:
    app.dependency_overrides[get_dashboard_service] = lambda: mock_dashboard_service
    app.dependency_overrides[get_current_user] = lambda: current_user
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test/api/v1")
    yield client
    app.dependency_overrides.clear()


class TestDashboardAPI:
    async def test_get_dashboard_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/dashboard")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "data" in body
        assert body["data"]["stats"]["total_interviews"] == 10

    async def test_get_dashboard_requires_auth(self, mock_dashboard_service: MagicMock) -> None:
        """Remove only the auth override to test 401 behaviour."""
        # Remove the get_current_user override so real guard runs (no token → 401)
        # Keep the service mock so the test doesn't need a real database.
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_dashboard_service] = lambda: mock_dashboard_service
        transport = ASGITransport(app=app)
        unauth_client = AsyncClient(transport=transport, base_url="http://test/api/v1")
        response = await unauth_client.get("/dashboard")
        assert response.status_code == 401
        # Restore the override for subsequent tests
        app.dependency_overrides[get_current_user] = lambda: _make_user()

    async def test_get_recent_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/dashboard/recent")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "interviews" in body["data"]
