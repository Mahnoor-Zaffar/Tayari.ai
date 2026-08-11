"""Regression tests for evaluation IDOR protection.

``GET /evaluations/{interview_id}`` must scope reads to the interview owner so
that an authenticated user cannot read another user's evaluation.  These tests
exercise the repository-level SQL scoping directly.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base
from features.auth.models import User as UserORM
from features.interview.models import Interview
from features.reports.models import Evaluation
from features.reports.repository import EvaluationRepository


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


def _add_user(session: AsyncSession, user_id: uuid.UUID, email: str) -> None:
    session.add(
        UserORM(
            id=user_id,
            email=email,
            username=email.split("@")[0],
            display_name="Test User",
            password_hash="$2b$12$placeholder",
        )
    )


async def _seed(session: AsyncSession, owner_id: uuid.UUID, other_id: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    """Seed owner/other users, an interview for the owner, and its evaluation."""
    _add_user(session, owner_id, "owner@example.com")
    _add_user(session, other_id, "other@example.com")

    interview = Interview(
        user_id=owner_id,
        type="coding",
        company="Google",
        role="Software Engineer",
        experience_level="mid-senior",
        language="python",
        difficulty="medium",
        duration_minutes=30,
    )
    session.add(interview)
    await session.flush()

    evaluation = Evaluation(
        interview_id=interview.id,
        overall_score=4.0,
        hire_verdict="hire",
        status="completed",
    )
    session.add(evaluation)
    await session.flush()

    return interview.id, evaluation.id


@pytest.mark.asyncio
async def test_owner_can_read_own_evaluation(session: AsyncSession) -> None:
    owner_id, other_id = uuid.uuid4(), uuid.uuid4()
    interview_id, _ = await _seed(session, owner_id, other_id)

    result = await EvaluationRepository(session).get_evaluation(interview_id, owner_id)

    assert result is not None
    assert result.interview_id == interview_id


@pytest.mark.asyncio
async def test_other_user_cannot_read_evaluation(session: AsyncSession) -> None:
    owner_id, other_id = uuid.uuid4(), uuid.uuid4()
    interview_id, _ = await _seed(session, owner_id, other_id)

    result = await EvaluationRepository(session).get_evaluation(interview_id, other_id)

    assert result is None
