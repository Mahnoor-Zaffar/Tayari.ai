from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base
from features.auth.domain.user import User, UserCreate
from features.auth.repositories import UserRepository


@pytest_asyncio.fixture(name="db_engine")
async def db_engine_fixture() -> AsyncGenerator:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(name="session")
async def session_fixture(db_engine) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(name="repository")
async def repository_fixture(session: AsyncSession) -> UserRepository:
    return UserRepository(session)


@pytest.fixture
def user_create() -> UserCreate:
    return UserCreate(
        email="alice@example.com",
        username="alice",
        display_name="Alice Smith",
        password_hash="$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qlq5yY1m1n1k1d1f1a1b1c1d1e1f",
    )


@pytest_asyncio.fixture(name="existing_user")
async def existing_user_fixture(
    repository: UserRepository,
    user_create: UserCreate,
) -> User:
    return await repository.create_user(user_create)
