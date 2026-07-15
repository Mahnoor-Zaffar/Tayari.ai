"""Enhanced interview session state machine.

Defines all valid states, transitions, and transition guards
for the complete interview session lifecycle.

States:
    IDLE        — Session created, awaiting initialization
    PREPARING   — Building AI context, loading prompts, fetching data
    ACTIVE      — Interview in progress, AI is asking questions
    PAUSED      — User paused the interview
    COMPLETING  — AI wrapping up, final question/remarks
    COMPLETED   — Interview finished, awaiting evaluation
    ARCHIVED    — Evaluation complete, session data persisted to long-term storage
    FAILED      — Irrecoverable error occurred
    TIMEOUT     — Session expired (duration exceeded + grace period)
"""

from __future__ import annotations

from enum import Enum


class SessionState(str, Enum):  # noqa: UP042
    IDLE = "idle"
    PREPARING = "preparing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"
    TIMEOUT = "timeout"


STATE_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.IDLE: {SessionState.PREPARING, SessionState.FAILED},
    SessionState.PREPARING: {SessionState.ACTIVE, SessionState.FAILED},
    SessionState.ACTIVE: {SessionState.PAUSED, SessionState.COMPLETING, SessionState.FAILED, SessionState.TIMEOUT},
    SessionState.PAUSED: {SessionState.ACTIVE, SessionState.COMPLETING, SessionState.FAILED, SessionState.TIMEOUT},
    SessionState.COMPLETING: {SessionState.COMPLETED, SessionState.FAILED},
    SessionState.COMPLETED: {SessionState.ARCHIVED, SessionState.FAILED},
    SessionState.ARCHIVED: set(),
    SessionState.FAILED: set(),
    SessionState.TIMEOUT: {SessionState.COMPLETED},
}


class TransitionGuard:
    """A callable predicate that can block a state transition."""

    def __init__(self, name: str, fn) -> None:
        self.name = name
        self._fn = fn

    def __call__(self, *args, **kwargs) -> bool:
        return self._fn(*args, **kwargs)

    def __repr__(self) -> str:
        return f"TransitionGuard({self.name})"


# ── Built-in guards ──────────────────────────────────────────────────────────

GUARD_SESSION_NOT_INITIALIZED = TransitionGuard(
    "session_not_initialized",
    lambda session: session.memory is None,
)

GUARD_ORCHESTRATOR_READY = TransitionGuard(
    "orchestrator_ready",
    lambda session: session.orchestrator is not None,
)


class InvalidTransitionError(ValueError):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, from_state: SessionState, to_state: SessionState, reason: str = "") -> None:
        self.from_state = from_state
        self.to_state = to_state
        msg = f"Cannot transition from {from_state.value} to {to_state.value}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


def validate_transition(from_state: SessionState, to_state: SessionState) -> None:
    """Raise InvalidTransitionError if the transition is not allowed."""
    allowed = STATE_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise InvalidTransitionError(from_state, to_state)


def is_terminal(state: SessionState) -> bool:
    """Return True if the state is terminal (no further transitions possible)."""
    return state in {SessionState.ARCHIVED, SessionState.FAILED}


def is_active(state: SessionState) -> bool:
    """Return True if the session is actively progressing."""
    return state in {SessionState.ACTIVE, SessionState.PREPARING, SessionState.COMPLETING}


def needs_recovery(state: SessionState) -> bool:
    """Return True if the session can be recovered from a disconnect."""
    return state in {SessionState.ACTIVE, SessionState.PAUSED, SessionState.PREPARING}
