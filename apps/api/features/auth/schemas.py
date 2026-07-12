from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ── Request ─────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# ── Response ────────────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    display_name: str
    email_verified: bool
    created_at: datetime


class AuthData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class SuccessResponse(BaseModel):
    success: bool = True
    data: AuthData
