"""Shared WebSocket authentication helpers.

WebSocket endpoints cannot use the standard ``Authorization`` header from a
browser, so clients present the access token inside the first protocol
message (``session.join`` / ``start``).  These helpers verify that token and
return the authenticated user id (or ``None``).
"""

from __future__ import annotations

from uuid import UUID

from features.auth.exceptions import InvalidTokenError
from features.auth.jwt.service import TokenService


async def verify_ws_token(token_service: TokenService, token: str) -> UUID | None:
    """Verify an access token and return the authenticated user id, or None."""
    if not token:
        return None
    try:
        payload = await token_service.verify(token, "access")
    except InvalidTokenError:
        return None
    try:
        return UUID(payload.sub)
    except (ValueError, AttributeError):
        return None
