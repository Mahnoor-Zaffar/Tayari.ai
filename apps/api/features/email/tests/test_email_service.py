"""Tests for the email service — HTML generation, API key guard, and send logic."""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from features.email.service import (
    _reset_email_html,
    _verify_email_html,
    send_reset_email,
    send_verification_email,
)


@pytest.fixture
def mock_resend():
    with patch("features.email.service.resend.Emails.send") as mock:
        mock.return_value = {"id": "test-id-123"}
        yield mock


class TestSendResetEmail:
    def test_sends_with_correct_args(self, mock_resend, monkeypatch):
        monkeypatch.setattr("features.email.service.settings.RESEND_API_KEY", "re_abc123")
        send_reset_email("alice@test.com", "https://example.com/reset?token=xyz")

        mock_resend.assert_called_once()
        call_kwargs = mock_resend.call_args[0][0]
        assert call_kwargs["to"] == "alice@test.com"
        assert call_kwargs["subject"] == "Reset your Tayari password"
        assert "https://example.com/reset?token=xyz" in call_kwargs["html"]

    def test_skips_when_api_key_missing(self, mock_resend, monkeypatch, caplog):
        monkeypatch.setattr("features.email.service.settings.RESEND_API_KEY", "")
        with caplog.at_level(logging.WARNING):
            send_reset_email("alice@test.com", "https://example.com/reset?token=xyz")

        mock_resend.assert_not_called()
        assert "RESEND_API_KEY not set" in caplog.text

    def test_logs_error_on_failure(self, mock_resend, monkeypatch, caplog):
        mock_resend.side_effect = Exception("API error")
        monkeypatch.setattr("features.email.service.settings.RESEND_API_KEY", "re_abc123")

        with caplog.at_level(logging.ERROR):
            send_reset_email("bob@test.com", "https://example.com/reset?token=abc")

        mock_resend.assert_called_once()
        assert "bob@test.com" in caplog.text
        assert "API error" in caplog.text


class TestSendVerificationEmail:
    def test_sends_with_correct_args(self, mock_resend, monkeypatch):
        monkeypatch.setattr("features.email.service.settings.RESEND_API_KEY", "re_abc123")
        send_verification_email("alice@test.com", "https://example.com/verify?token=xyz")

        mock_resend.assert_called_once()
        call_kwargs = mock_resend.call_args[0][0]
        assert call_kwargs["to"] == "alice@test.com"
        assert call_kwargs["subject"] == "Verify your Tayari email address"
        assert "https://example.com/verify?token=xyz" in call_kwargs["html"]

    def test_skips_when_api_key_missing(self, mock_resend, monkeypatch, caplog):
        monkeypatch.setattr("features.email.service.settings.RESEND_API_KEY", "")
        with caplog.at_level(logging.WARNING):
            send_verification_email("alice@test.com", "https://example.com/verify?token=xyz")

        mock_resend.assert_not_called()
        assert "RESEND_API_KEY not set" in caplog.text

    def test_logs_error_on_failure(self, mock_resend, monkeypatch, caplog):
        mock_resend.side_effect = Exception("Timeout")
        monkeypatch.setattr("features.email.service.settings.RESEND_API_KEY", "re_abc123")

        with caplog.at_level(logging.ERROR):
            send_verification_email("carol@test.com", "https://example.com/verify?token=def")

        mock_resend.assert_called_once()
        assert "carol@test.com" in caplog.text


class TestHtmlTemplates:
    def test_reset_html_contains_url(self):
        url = "https://example.com/reset?token=secret123"
        html = _reset_email_html(url)

        assert url in html
        assert "Reset Password" in html
        assert "<!DOCTYPE html>" in html

    def test_verify_html_contains_url(self):
        url = "https://example.com/verify?token=secret456"
        html = _verify_email_html(url)

        assert url in html
        assert "Verify Email" in html
        assert "<!DOCTYPE html>" in html

    def test_reset_html_expiry_stated(self):
        html = _reset_email_html("https://example.com/reset?token=x")
        assert "1 hour" in html

    def test_verify_html_expiry_stated(self):
        html = _verify_email_html("https://example.com/verify?token=x")
        assert "24 hours" in html
