"""Tests for the interview session state machine."""

from __future__ import annotations

import pytest

from ai.realtime.state_machine import (
    STATE_TRANSITIONS,
    InvalidTransitionError,
    SessionState,
    is_active,
    is_terminal,
    needs_recovery,
    validate_transition,
)


class TestStateMachine:
    def test_pending_can_transition_to_initializing(self):
        validate_transition(SessionState.IDLE, SessionState.PREPARING)

    def test_pending_can_transition_to_failed(self):
        validate_transition(SessionState.IDLE, SessionState.FAILED)

    def test_pending_cannot_skip_to_active(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(SessionState.IDLE, SessionState.ACTIVE)

    def test_initializing_transitions_to_active(self):
        validate_transition(SessionState.PREPARING, SessionState.ACTIVE)

    def test_initializing_can_fail(self):
        validate_transition(SessionState.PREPARING, SessionState.FAILED)

    def test_active_can_pause(self):
        validate_transition(SessionState.ACTIVE, SessionState.PAUSED)

    def test_active_can_complete(self):
        validate_transition(SessionState.ACTIVE, SessionState.COMPLETING)

    def test_active_can_timeout(self):
        validate_transition(SessionState.ACTIVE, SessionState.TIMEOUT)

    def test_paused_can_resume(self):
        validate_transition(SessionState.PAUSED, SessionState.ACTIVE)

    def test_paused_can_complete(self):
        validate_transition(SessionState.PAUSED, SessionState.COMPLETING)

    def test_completing_transitions_to_completed(self):
        validate_transition(SessionState.COMPLETING, SessionState.COMPLETED)

    def test_completed_is_not_terminal(self):
        assert not is_terminal(SessionState.COMPLETED)
        assert is_terminal(SessionState.ARCHIVED)

    def test_failed_is_terminal(self):
        assert is_terminal(SessionState.FAILED)

    def test_active_is_not_terminal(self):
        assert not is_terminal(SessionState.ACTIVE)

    def test_is_active_returns_true_for_active(self):
        assert is_active(SessionState.ACTIVE)

    def test_is_active_returns_false_for_paused(self):
        assert not is_active(SessionState.PAUSED)

    def test_needs_recovery_returns_true_for_active(self):
        assert needs_recovery(SessionState.ACTIVE)

    def test_needs_recovery_returns_false_for_completed(self):
        assert not needs_recovery(SessionState.COMPLETED)

    def test_completed_has_transitions_to_archived_or_failed(self):
        assert len(STATE_TRANSITIONS[SessionState.COMPLETED]) == 2
        assert SessionState.ARCHIVED in STATE_TRANSITIONS[SessionState.COMPLETED]
        assert SessionState.FAILED in STATE_TRANSITIONS[SessionState.COMPLETED]

    def test_failed_has_no_transitions(self):
        assert len(STATE_TRANSITIONS[SessionState.FAILED]) == 0

    def test_invalid_transition_error_message(self):
        err = InvalidTransitionError(SessionState.IDLE, SessionState.ACTIVE)
        assert "idle" in str(err)
        assert "active" in str(err)



