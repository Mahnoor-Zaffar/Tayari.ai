"""Tests for the event dispatcher."""

from __future__ import annotations

import pytest

from ai.realtime.event_dispatcher import EVENT_SESSION_CREATED, EVENT_SESSION_STARTED, EventDispatcher


@pytest.mark.asyncio
class TestEventDispatcher:
    async def test_subscribe_and_emit(self):
        dispatcher = EventDispatcher()
        received: list[tuple[str, str, dict]] = []

        async def handler(session_id: str, event_type: str, payload: dict) -> None:
            received.append((session_id, event_type, payload))

        dispatcher.subscribe(EVENT_SESSION_CREATED, handler)
        await dispatcher.emit("session-1", EVENT_SESSION_CREATED, {"foo": "bar"})

        assert len(received) == 1
        assert received[0][0] == "session-1"
        assert received[0][1] == EVENT_SESSION_CREATED
        assert received[0][2] == {"foo": "bar"}

    async def test_unsubscribe(self):
        dispatcher = EventDispatcher()
        received: list[str] = []

        async def handler(session_id: str, event_type: str, payload: dict) -> None:
            received.append(session_id)

        dispatcher.subscribe(EVENT_SESSION_CREATED, handler)
        dispatcher.unsubscribe(EVENT_SESSION_CREATED, handler)
        await dispatcher.emit("session-1", EVENT_SESSION_CREATED)
        assert len(received) == 0

    async def test_multiple_subscribers(self):
        dispatcher = EventDispatcher()
        results: list[str] = []

        async def handler1(session_id: str, event_type: str, payload: dict) -> None:
            results.append("h1")

        async def handler2(session_id: str, event_type: str, payload: dict) -> None:
            results.append("h2")

        dispatcher.subscribe(EVENT_SESSION_STARTED, handler1)
        dispatcher.subscribe(EVENT_SESSION_STARTED, handler2)
        await dispatcher.emit("s1", EVENT_SESSION_STARTED)
        assert len(results) == 2
        assert results == ["h1", "h2"]

    async def test_emit_to_unsubscribed_event_does_not_raise(self):
        dispatcher = EventDispatcher()
        await dispatcher.emit("s1", "nonexistent.event")

    async def test_handler_exception_does_not_propagate(self):
        dispatcher = EventDispatcher()

        async def failing_handler(session_id: str, event_type: str, payload: dict) -> None:
            raise ValueError("fail")

        dispatcher.subscribe(EVENT_SESSION_CREATED, failing_handler)
        await dispatcher.emit("s1", EVENT_SESSION_CREATED)
