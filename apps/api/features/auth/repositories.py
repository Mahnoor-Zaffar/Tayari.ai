from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from features.auth.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def save(self, user: User) -> User:
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID, *, include_deleted: bool = False) -> User | None:
        stmt = self._active_query(include_deleted).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, email: str, *, include_deleted: bool = False) -> User | None:
        stmt = self._active_query(include_deleted).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_username(self, username: str, *, include_deleted: bool = False) -> User | None:
        stmt = self._active_query(include_deleted).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_active(self, *, offset: int = 0, limit: int = 100) -> Sequence[User]:
        stmt = (
            self._active_query(include_deleted=False)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def soft_delete(self, user: User) -> User:
        user.deleted_at = datetime.now(UTC)
        user.is_active = False
        return await self.save(user)

    async def exists_by_email(self, email: str, *, include_deleted: bool = False) -> bool:
        stmt = select(func.count()).select_from(User).where(User.email == email)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def exists_by_username(self, username: str, *, include_deleted: bool = False) -> bool:
        stmt = select(func.count()).select_from(User).where(User.username == username)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def count_active(self) -> int:
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.deleted_at.is_(None), User.is_active.is_(True))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _active_query(self, include_deleted: bool) -> Select:
        stmt = select(User)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return stmt
