from datetime import datetime

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """Validated token payload returned by ``TokenService.verify()``.

    Every field is guaranteed to exist after verification — the decode step
    requires all standard claims via ``require``, and the ``type`` claim is
    validated against the expected value.
    """

    sub: str
    type: str
    exp: datetime
    iat: datetime
    jti: str
    iss: str
    aud: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    token_family: str | None = Field(default=None)
