from datetime import datetime
from typing import Protocol


class TokenBlacklistProtocol(Protocol):
    """Contract for token revocation storage.

    Implementations can use Redis (TTL-aligned key expiry), a database
    table, or an in-memory set for testing.
    """

    async def add(self, jti: str, expires_at: datetime) -> None:
        """Mark *jti* as revoked until *expires_at*."""

    async def is_blacklisted(self, jti: str) -> bool:
        """Return ``True`` if *jti* has been revoked."""
