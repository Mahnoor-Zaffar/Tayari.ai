from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    display_name: str
    password_hash: str
    email_verified: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class UserCreate(BaseModel):
    email: str
    username: str
    display_name: str
    password_hash: str


class UserUpdate(BaseModel):
    email: str | None = None
    username: str | None = None
    display_name: str | None = None
    password_hash: str | None = None
    email_verified: bool | None = None
    is_active: bool | None = None
