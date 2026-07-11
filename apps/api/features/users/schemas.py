from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UpdateUserRequest(BaseModel):
    display_name: str | None = None
    experience_level: str | None = None
    avatar_url: str | None = None


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    experience_level: str | None = None
    avatar_url: str | None = None
    email_verified: bool = False
    created_at: datetime
