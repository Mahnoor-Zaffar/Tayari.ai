"""In-process event dispatcher.

Simple Pub/Sub for session lifecycle events.
Subscribers are async callbacks registered by event type.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)

EventHandler = Callable[[str, str, dict[str, Any]], Coroutine[Any, Any, None]]


class EventDispatcher:
    """In-process pub/sub for session events.

    Events are tuples of (session_id, event_type, payload).
    Subscribers are async callbacks that receive all three.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        self._subscribers[event_type].append(handler)
        logger.debug("Subscribed handler for event: %s", event_type)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler for a specific event type."""
        self._subscribers[event_type] = [h for h in self._subscribers[event_type] if h is not handler]

    async def emit(self, session_id: str, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Emit an event to all subscribers."""
        payload = payload or {}
        logger.info("Event: session=%s type=%s", session_id[:8], event_type)
        tasks = []
        for handler in self._subscribers.get(event_type, []):
            tasks.append(handler(session_id, event_type, payload))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def emit_to_all(self, session_id: str, event_types: list[str], payload: dict[str, Any] | None = None) -> None:
        """Emit the same payload to multiple event types."""
        for event_type in event_types:
            await self.emit(session_id, event_type, payload)


# ── Session lifecycle events ──────────────────────────────────────────────────

EVENT_SESSION_CREATED = "session.created"
EVENT_SESSION_PREPARING = "session.preparing"
EVENT_SESSION_STARTED = "session.started"
EVENT_SESSION_PAUSED = "session.paused"
EVENT_SESSION_RESUMED = "session.resumed"
EVENT_SESSION_COMPLETING = "session.completing"
EVENT_SESSION_COMPLETED = "session.completed"
EVENT_SESSION_ARCHIVED = "session.archived"
EVENT_SESSION_FAILED = "session.failed"
EVENT_SESSION_TIMEOUT = "session.timeout"

# ── Interview turn events ────────────────────────────────────────────────────

EVENT_QUESTION_ASKED = "question.asked"
EVENT_ANSWER_RECEIVED = "answer.received"
EVENT_HINT_REQUESTED = "hint.requested"
EVENT_HINT_GENERATED = "hint.generated"

# ── Connection events ────────────────────────────────────────────────────────

EVENT_CLIENT_CONNECTED = "client.connected"
EVENT_CLIENT_DISCONNECTED = "client.disconnected"
EVENT_HEARTBEAT_MISSED = "heartbeat.missed"
EVENT_HEARTBEAT_RESTORED = "heartbeat.restored"
EVENT_RECONNECTED = "session.reconnected"

# ── System events ────────────────────────────────────────────────────────────

EVENT_AI_LATENCY_HIGH = "ai.latency_high"
EVENT_AI_GENERATED = "ai.generated"
EVENT_AI_FAILED = "ai.failed"
EVENT_TRANSCRIPT_SEGMENT = "transcript.segment"
EVENT_EVALUATION_READY = "evaluation.ready"
EVENT_EVALUATION_FAILED = "evaluation.failed"

# ── All event types for subscription management ──────────────────────────────

ALL_EVENTS: list[str] = [
    EVENT_SESSION_CREATED,
    EVENT_SESSION_PREPARING,
    EVENT_SESSION_STARTED,
    EVENT_SESSION_PAUSED,
    EVENT_SESSION_RESUMED,
    EVENT_SESSION_COMPLETING,
    EVENT_SESSION_COMPLETED,
    EVENT_SESSION_ARCHIVED,
    EVENT_SESSION_FAILED,
    EVENT_SESSION_TIMEOUT,
    EVENT_QUESTION_ASKED,
    EVENT_ANSWER_RECEIVED,
    EVENT_HINT_REQUESTED,
    EVENT_HINT_GENERATED,
    EVENT_CLIENT_CONNECTED,
    EVENT_CLIENT_DISCONNECTED,
    EVENT_HEARTBEAT_MISSED,
    EVENT_HEARTBEAT_RESTORED,
    EVENT_RECONNECTED,
    EVENT_AI_LATENCY_HIGH,
    EVENT_AI_GENERATED,
    EVENT_AI_FAILED,
    EVENT_TRANSCRIPT_SEGMENT,
    EVENT_EVALUATION_READY,
    EVENT_EVALUATION_FAILED,
]
