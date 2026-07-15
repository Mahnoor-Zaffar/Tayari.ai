"""Tests for the transcript analyzer."""

from __future__ import annotations

from evaluation.transcript_analyzer import TranscriptAnalyzer


class TestTranscriptAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = TranscriptAnalyzer()

    def test_empty_transcript(self):
        result = self.analyzer.analyze([])
        assert result["total_turns"] == 0
        assert result["total_words"] == 0

    def test_single_turn(self):
        transcript = [{"speaker": "ai", "text": "Hello, welcome to the interview."}]
        result = self.analyzer.analyze(transcript)
        assert result["total_turns"] == 1
        assert result["ai_turns"] == 1
        assert result["user_turns"] == 0

    def test_multiple_turns(self):
        transcript = [
            {"speaker": "ai", "text": "Tell me about yourself."},
            {"speaker": "user", "text": "I am a software engineer with 5 years of experience."},
            {"speaker": "ai", "text": "Great, let's discuss a system design problem."},
        ]
        result = self.analyzer.analyze(transcript)
        assert result["total_turns"] == 3
        assert result["ai_turns"] == 2
        assert result["user_turns"] == 1

    def test_word_count(self):
        transcript = [
            {"speaker": "ai", "text": "Hello world"},
            {"speaker": "user", "text": "Hi there, how are you?"},
        ]
        result = self.analyzer.analyze(transcript)
        assert result["ai_word_count"] == 2
        assert result["user_word_count"] == 5
        assert result["total_words"] == 7

    def test_format_for_prompt(self):
        transcript = [
            {"speaker": "ai", "text": "Welcome!"},
            {"speaker": "user", "text": "Thanks!"},
        ]
        formatted = self.analyzer.format_for_prompt(transcript)
        assert "Interviewer: Welcome!" in formatted
        assert "Candidate: Thanks!" in formatted

    def test_pause_detection(self):
        transcript = [
            {"speaker": "ai", "text": "Question?", "timestamp_ms": 0},
            {"speaker": "user", "text": "Answer", "timestamp_ms": 5000},
            {"speaker": "ai", "text": "Follow-up", "timestamp_ms": 5001},
        ]
        result = self.analyzer.analyze(transcript)
        assert result["total_pause_ms"] >= 4000
