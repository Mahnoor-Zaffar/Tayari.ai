"""Shared fixtures for the interview test suite.

Mirrors the pattern from ``features/auth/tests/conftest.py`` and
``features/analytics/tests/test_analytics.py``: in-memory SQLite for
speed, JSONB ( silly patch for SQLite compatibility, and seeded user.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import JSON, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base
from features.auth.models import User as UserORM
from features.interview.repository import InterviewRepository


@event.listens_for(Base.metadata, "before_create")
def _compile_jsonb_for_sqlite(target, connection, **kw):
    if connection.engine.dialect.name == "sqlite":
        for table in target.tables.values():
            for column in table.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()


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
async def repository_fixture(session: AsyncSession) -> InterviewRepository:
    return InterviewRepository(session)


@pytest_asyncio.fixture(name="seeded_user_id")
async def seeded_user_id_fixture(session: AsyncSession) -> uuid.UUID:
    """Seed a user and return its ID for repository tests."""
    user_id = uuid.uuid4()
    session.add(
        UserORM(
            id=user_id,
            email="test@example.com",
            username="testuser",
            display_name="Test User",
            password_hash="$2b$12$placeholder",
        )
    )
    await session.flush()
    return user_id
