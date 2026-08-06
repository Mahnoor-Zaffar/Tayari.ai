from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# JSONB on PostgreSQL, generic JSON everywhere else (e.g. SQLite tests).
JSONBType = JSON().with_variant(JSONB, "postgresql")

# Native UUID on PostgreSQL, CHAR(32) on SQLite. The postgresql UUID type alone
# is unsafe on SQLite: the bare "UUID" type name gets NUMERIC affinity there, so
# all-numeric UUIDs (e.g. 00000000-...-0001 test fixtures) are stored as ints.
UUIDType = Uuid(as_uuid=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            if session.is_active:
                await session.commit()
        except Exception:
            if session.is_active:
                await session.rollback()
            raise
        finally:
            await session.close()
