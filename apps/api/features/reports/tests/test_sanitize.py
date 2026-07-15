"""Tests for the evaluation sanitization module."""

from __future__ import annotations

from evaluation.sanitize import sanitize_source_code, sanitize_transcript


class TestSanitizeTranscript:
    def test_redacts_email(self):
        result = sanitize_transcript("Contact me at john@example.com")
        assert "[EMAIL]" in result
        assert "john@example.com" not in result

    def test_redacts_phone(self):
        result = sanitize_transcript("Call 555-123-4567 for details")
        assert "[PHONE]" in result
        assert "555-123-4567" not in result

    def test_redacts_ssn(self):
        result = sanitize_transcript("My SSN is 123-45-6789")
        assert "[SSN]" in result
        assert "123-45-6789" not in result

    def test_redacts_url(self):
        result = sanitize_transcript("Visit https://example.com/path?q=1")
        assert "[URL]" in result
        assert "example.com" not in result

    def test_removes_control_chars(self):
        result = sanitize_transcript("hello\x00world\x01test")
        assert "\x00" not in result
        assert "\x01" not in result
        assert "helloworldtest" in result.replace(" ", "")

    def test_truncates_long_transcript(self):
        long_text = "a" * 60_000
        result = sanitize_transcript(long_text)
        assert len(result) <= 50_000

    def test_preserves_normal_text(self):
        result = sanitize_transcript("Hello, this is a normal interview answer.")
        assert "Hello, this is a normal interview answer." in result

    def test_empty_transcript(self):
        assert sanitize_transcript("") == ""


class TestSanitizeSourceCode:
    def test_truncates_long_code(self):
        long_code = "x = 1\n" * 10_000
        result = sanitize_source_code(long_code)
        assert len(result) <= 10_000

    def test_preserves_normal_code(self):
        code = "def solve():\n    return 42"
        result = sanitize_source_code(code)
        assert result == code
