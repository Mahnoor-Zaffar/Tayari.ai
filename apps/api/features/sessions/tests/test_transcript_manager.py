"""Tests for the transcript manager."""

from __future__ import annotations

from ai.realtime.transcript_manager import TranscriptManager, TranscriptSegment


class TestTranscriptManager:
    def test_empty_transcript(self):
        tm = TranscriptManager()
        assert tm.get_transcript() == []
        assert tm.full_text == ""
        assert tm.segment_count == 0

    def test_append_static(self):
        tm = TranscriptManager()
        seg = tm.append_static("ai", "Hello, welcome.")
        assert isinstance(seg, TranscriptSegment)
        assert seg.speaker == "ai"
        assert seg.text == "Hello, welcome."
        assert tm.segment_count == 1

    def test_append_and_commit_partial(self):
        tm = TranscriptManager()
        tm.append_partial("I think we")
        tm.append_partial("I think we should use")
        seg = tm.commit_partial("user")
        assert seg.speaker == "user"
        assert seg.text == "I think we should use"
        assert seg.is_final is True
        assert tm.segment_count == 1
        assert tm._partial == ""

    def test_full_text_concatenation(self):
        tm = TranscriptManager()
        tm.append_static("ai", "Question 1")
        tm.append_static("user", "Answer 1")
        tm.append_static("ai", "Question 2")
        assert "Question 1" in tm.full_text
        assert "Answer 1" in tm.full_text
        assert "Question 2" in tm.full_text

    def test_get_transcript_structure(self):
        tm = TranscriptManager()
        tm.append_static("ai", "Hi", timestamp_ms=100)
        transcript = tm.get_transcript()
        assert len(transcript) == 1
        assert transcript[0]["speaker"] == "ai"
        assert transcript[0]["text"] == "Hi"
        assert transcript[0]["timestamp_ms"] == 100
        assert transcript[0]["is_final"] is True

    def test_reset(self):
        tm = TranscriptManager()
        tm.append_static("ai", "Hello")
        tm.reset()
        assert tm.segment_count == 0
        assert tm._partial == ""
