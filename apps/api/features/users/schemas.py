from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UpdateUserRequest(BaseModel):
    display_name: str | None = None
    is_active: bool | None = None


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    email_verified: bool = False
    created_at: datetime


class UserAdminResponse(BaseModel):
    id: UUID
    email: str
    username: str
    display_name: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: list[UserAdminResponse]
    total: int
    skip: int
    limit: int
