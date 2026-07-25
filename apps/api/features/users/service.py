"""User service for admin operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from features.users.repository import UserRepository
from features.users.schemas import UpdateUserRequest, UserAdminResponse, UserListResponse


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> UserListResponse:
        users, total = await self._repo.list_users(skip=skip, limit=limit, search=search)
        return UserListResponse(
            users=[UserAdminResponse.model_validate(u) for u in users],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_user(self, user_id: UUID) -> UserAdminResponse | None:
        user = await self._repo.find_by_id(user_id)
        return UserAdminResponse.model_validate(user) if user else None

    async def update_user(self, user_id: UUID, data: UpdateUserRequest) -> UserAdminResponse | None:
        user = await self._repo.update_user(user_id, data.model_dump(exclude_unset=True, exclude_none=True))
        return UserAdminResponse.model_validate(user) if user else None

    async def delete_user(self, user_id: UUID) -> None:
        await self._repo.soft_delete(user_id)

    async def get_stats(self) -> dict:
        total = await self._repo.count_users()
        inactive = await self._repo.count_inactive()
        return {
            "total_users": total,
            "active_users": total - inactive,
            "inactive_users": inactive,
        }
