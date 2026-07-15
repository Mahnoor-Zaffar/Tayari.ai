"""Pydantic schemas for the sessions feature.

Includes REST request/response models and WebSocket message schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# ── REST Request Models ──────────────────────────────────────────────────────


class StartInterviewRequest(BaseModel):
    """POST /sessions body — starts a new interview session."""

    interview_id: UUID


class SessionStatusResponse(BaseModel):
    """Current session status."""

    session_id: str
    interview_id: str
    user_id: str
    state: str
    elapsed_seconds: int = 0
    remaining_seconds: int = 0
    total_paused_seconds: int = 0
    disconnect_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None
    created_at: datetime | None = None


# ── WebSocket Message Schemas ────────────────────────────────────────────────


class WSMessage(BaseModel):
    """Base WebSocket message envelope."""

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


# Client → Server
class JoinMessage(WSMessage):
    type: Literal["session.join"] = "session.join"
    payload: dict[str, Any]  # { session_id, token }


class UserAnswerMessage(WSMessage):
    type: Literal["user.answer"] = "user.answer"
    payload: dict[str, Any]  # { text, timestamp_ms }


class UserCodeMessage(WSMessage):
    type: Literal["user.code"] = "user.code"
    payload: dict[str, Any]  # { code, language, cursor_position }


class PauseMessage(WSMessage):
    type: Literal["session.pause"] = "session.pause"
    payload: dict[str, Any] = Field(default_factory=dict)


class ResumeMessage(WSMessage):
    type: Literal["session.resume"] = "session.resume"
    payload: dict[str, Any] = Field(default_factory=dict)


class HintRequestMessage(WSMessage):
    type: Literal["session.request_hint"] = "session.request_hint"
    payload: dict[str, Any] = Field(default_factory=dict)


class MediaStreamReadyMessage(WSMessage):
    type: Literal["media.stream_ready"] = "media.stream_ready"
    payload: dict[str, Any]  # { sdp, ice_candidates[] }


class HeartbeatMessage(WSMessage):
    type: Literal["heartbeat"] = "heartbeat"
    payload: dict[str, Any] = Field(default_factory=dict)


# Server → Client
class ServerMessage(BaseModel):
    """Server-sent WebSocket message."""

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


# ── Event Sequence (for reconnect replay) ────────────────────────────────────


class EventEntry(BaseModel):
    """A single event from the session event log."""

    id: str
    session_id: str
    interview_id: str
    event_type: str
    payload: dict[str, Any]
    sequence: int
    created_at: str


class EventReplayResponse(BaseModel):
    """Returned on reconnection — missed events to replay."""

    events: list[EventEntry]
    latest_state: str
    remaining_seconds: int
