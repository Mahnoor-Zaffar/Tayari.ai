from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from features.auth.domain.user import User, UserCreate, UserUpdate
from features.auth.models import User as UserORM


class NotFoundError(Exception):
    pass


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_user(self, data: UserCreate) -> User:
        user = UserORM(**data.model_dump())
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return User.model_validate(user)

    async def find_by_id(self, user_id: UUID, *, include_deleted: bool = False) -> User | None:
        stmt = self._active_query(include_deleted).where(UserORM.id == user_id)
        result = await self._session.execute(stmt)
        user_orm = result.unique().scalar_one_or_none()
        return User.model_validate(user_orm) if user_orm else None

    async def find_by_email(self, email: str, *, include_deleted: bool = False) -> User | None:
        stmt = self._active_query(include_deleted).where(UserORM.email == email)
        result = await self._session.execute(stmt)
        user_orm = result.unique().scalar_one_or_none()
        return User.model_validate(user_orm) if user_orm else None

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        result = await self._session.execute(select(UserORM).where(UserORM.id == user_id, UserORM.deleted_at.is_(None)))
        user_orm = result.unique().scalar_one_or_none()
        if user_orm is None:
            raise NotFoundError(f"User {user_id} not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user_orm, field, value)
        await self._session.flush()
        await self._session.refresh(user_orm)
        return User.model_validate(user_orm)

    async def delete_user(self, user_id: UUID) -> None:
        result = await self._session.execute(select(UserORM).where(UserORM.id == user_id, UserORM.deleted_at.is_(None)))
        user_orm = result.unique().scalar_one_or_none()
        if user_orm is None:
            return
        user_orm.deleted_at = datetime.now(UTC)
        user_orm.is_active = False
        await self._session.flush()

    async def exists(
        self, *, email: str | None = None, username: str | None = None, include_deleted: bool = False
    ) -> bool:
        stmt = select(func.count()).select_from(UserORM)
        if email is not None:
            stmt = stmt.where(UserORM.email == email)
        if username is not None:
            stmt = stmt.where(UserORM.username == username)
        if not include_deleted:
            stmt = stmt.where(UserORM.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    def _active_query(self, include_deleted: bool) -> Select:
        stmt = select(UserORM)
        if not include_deleted:
            stmt = stmt.where(UserORM.deleted_at.is_(None))
        return stmt
