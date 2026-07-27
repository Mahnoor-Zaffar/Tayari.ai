"""Tests for the session state machine — no DB, no mocks needed."""

import pytest

from ai.realtime.state_machine import (
    InvalidTransitionError,
    SessionState,
    is_active,
    is_terminal,
    needs_recovery,
    validate_transition,
)


class TestSessionState:
    def test_idle_can_prepare(self):
        validate_transition(SessionState.IDLE, SessionState.PREPARING)

    def test_preparing_can_start(self):
        validate_transition(SessionState.PREPARING, SessionState.ACTIVE)

    def test_active_can_pause(self):
        validate_transition(SessionState.ACTIVE, SessionState.PAUSED)

    def test_paused_can_resume(self):
        validate_transition(SessionState.PAUSED, SessionState.ACTIVE)

    def test_active_can_complete(self):
        validate_transition(SessionState.ACTIVE, SessionState.COMPLETING)
        validate_transition(SessionState.COMPLETING, SessionState.COMPLETED)

    def test_completed_can_archive(self):
        validate_transition(SessionState.COMPLETED, SessionState.ARCHIVED)

    def test_idle_can_fail(self):
        validate_transition(SessionState.IDLE, SessionState.FAILED)

    def test_any_can_timeout(self):
        validate_transition(SessionState.ACTIVE, SessionState.TIMEOUT)

    def test_invalid_transition_raises(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionState.IDLE, SessionState.COMPLETED)

    def test_cannot_complete_from_idle(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionState.IDLE, SessionState.COMPLETING)

    def test_cannot_resume_from_idle(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionState.IDLE, SessionState.ACTIVE)

    def test_terminal_states(self):
        assert is_terminal(SessionState.FAILED)
        assert is_terminal(SessionState.ARCHIVED)
        assert not is_terminal(SessionState.COMPLETED)
        assert not is_terminal(SessionState.ACTIVE)
        assert not is_terminal(SessionState.IDLE)

    def test_active_states(self):
        assert is_active(SessionState.ACTIVE)
        assert not is_active(SessionState.IDLE)
        assert not is_active(SessionState.COMPLETED)

    def test_needs_recovery(self):
        assert needs_recovery(SessionState.ACTIVE)
        assert needs_recovery(SessionState.PAUSED)
        assert not needs_recovery(SessionState.COMPLETED)
        assert not needs_recovery(SessionState.FAILED)
        assert not needs_recovery(SessionState.ARCHIVED)
