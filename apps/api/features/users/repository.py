"""User repository for admin operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from features.auth.domain.user import User
from features.auth.models import User as UserORM


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(UserORM).where(UserORM.deleted_at.is_(None)).order_by(UserORM.created_at.desc())

        count_stmt = select(func.count()).select_from(UserORM).where(UserORM.deleted_at.is_(None))

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                UserORM.email.ilike(pattern) | UserORM.display_name.ilike(pattern) | UserORM.username.ilike(pattern)
            )
            count_stmt = count_stmt.where(
                UserORM.email.ilike(pattern) | UserORM.display_name.ilike(pattern) | UserORM.username.ilike(pattern)
            )

        total = (await self._session.execute(count_stmt)).scalar_one()

        result = await self._session.execute(stmt.offset(skip).limit(limit))
        users = [User.model_validate(row) for row in result.unique().scalars()]
        return users, total

    async def find_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserORM).where(UserORM.id == user_id, UserORM.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        user_orm = result.unique().scalar_one_or_none()
        return User.model_validate(user_orm) if user_orm else None

    async def update_user(self, user_id: UUID, data: dict) -> User:
        stmt = select(UserORM).where(UserORM.id == user_id, UserORM.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        user_orm = result.unique().scalar_one_or_none()
        if user_orm is None:
            raise ValueError(f"User {user_id} not found")
        for field, value in data.items():
            if hasattr(user_orm, field):
                setattr(user_orm, field, value)
        await self._session.flush()
        await self._session.refresh(user_orm)
        return User.model_validate(user_orm)

    async def soft_delete(self, user_id: UUID) -> None:
        from datetime import UTC, datetime

        stmt = select(UserORM).where(UserORM.id == user_id, UserORM.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        user_orm = result.unique().scalar_one_or_none()
        if user_orm is None:
            return
        user_orm.deleted_at = datetime.now(UTC)
        user_orm.is_active = False
        await self._session.flush()

    async def count_users(self) -> int:
        stmt = select(func.count()).select_from(UserORM).where(UserORM.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_inactive(self) -> int:
        stmt = select(func.count()).select_from(UserORM).where(UserORM.deleted_at.is_(None), ~UserORM.is_active)
        result = await self._session.execute(stmt)
        return result.scalar_one()
