"""Heartbeat monitoring for active interview sessions.

Tracks last heartbeat time per session and emits
heartbeat.missed events when a threshold is exceeded.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from ai.realtime.event_dispatcher import EVENT_HEARTBEAT_MISSED, EventDispatcher

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_S = 10
HEARTBEAT_TIMEOUT_S = 30
CHECK_INTERVAL_S = 15


@dataclass
class HeartbeatRecord:
    session_id: str
    last_heartbeat: float = field(default_factory=time.time)
    missed_count: int = 0


class HeartbeatMonitor:
    """Monitors heartbeat for active sessions.

    Runs a background task that periodically checks
    if sessions have missed their heartbeat threshold.
    """

    def __init__(self, dispatcher: EventDispatcher) -> None:
        self._dispatcher = dispatcher
        self._sessions: dict[str, HeartbeatRecord] = {}
        self._task: asyncio.Task | None = None
        self._running = False

    def register(self, session_id: str) -> None:
        """Register a session for heartbeat monitoring."""
        self._sessions[session_id] = HeartbeatRecord(session_id=session_id)
        logger.debug("Heartbeat registered: %s", session_id[:8])

    def unregister(self, session_id: str) -> None:
        """Remove a session from heartbeat monitoring."""
        self._sessions.pop(session_id, None)
        logger.debug("Heartbeat unregistered: %s", session_id[:8])

    def record_heartbeat(self, session_id: str) -> None:
        """Record a heartbeat for a session."""
        record = self._sessions.get(session_id)
        if record:
            record.last_heartbeat = time.time()
            record.missed_count = 0

    def start(self) -> None:
        """Start the background heartbeat checker."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("Heartbeat monitor started")

    async def stop(self) -> None:
        """Stop the background heartbeat checker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat monitor stopped")

    async def _check_loop(self) -> None:
        while self._running:
            await asyncio.sleep(CHECK_INTERVAL_S)
            now = time.time()
            stale_sessions = []
            for session_id, record in list(self._sessions.items()):
                elapsed = now - record.last_heartbeat
                if elapsed > HEARTBEAT_TIMEOUT_S:
                    stale_sessions.append((session_id, record))

            for session_id, record in stale_sessions:
                record.missed_count += 1
                logger.warning("Heartbeat missed: session=%s count=%d", session_id[:8], record.missed_count)
                await self._dispatcher.emit(
                    session_id,
                    EVENT_HEARTBEAT_MISSED,
                    {"missed_count": record.missed_count, "elapsed_seconds": now - record.last_heartbeat},
                )

    @property
    def active_count(self) -> int:
        return len(self._sessions)
