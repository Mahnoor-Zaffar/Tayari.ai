"""In-memory token blacklist for development — trades durability for simplicity.

In production, swap for a Redis-backed ``TokenBlacklistProtocol`` that
leverages TTL-based key expiry.
"""

from datetime import UTC, datetime

from features.auth.jwt.interfaces import TokenBlacklistProtocol


class MemoryBlacklist(TokenBlacklistProtocol):
    """Thread-safe in-memory blacklist.

    Blacklisted JTIs (and token families) are stored in a plain dict
    with their expiry timestamp.  ``is_blacklisted`` prunes expired
    entries on each call.
    """

    def __init__(self) -> None:
        self._store: dict[str, datetime] = {}

    async def add(self, jti: str, expires_at: datetime) -> None:
        self._store[jti] = expires_at

    async def is_blacklisted(self, jti: str) -> bool:
        self._prune()
        return jti in self._store

    def _prune(self) -> None:
        now = datetime.now(UTC)
        expired = [k for k, v in self._store.items() if v <= now]
        for k in expired:
            del self._store[k]
