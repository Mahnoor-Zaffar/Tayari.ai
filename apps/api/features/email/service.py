"""Email service using Resend API."""

from __future__ import annotations

import logging

import resend

from core.config import settings

logger = logging.getLogger(__name__)

_SENDER = "Tayari AI <noreply@tayari.ai>"


def _send_email(to: str, subject: str, html: str) -> None:
    """Low-level email send via Resend.

    Synchronous — Resend's SDK does not provide an async interface.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email to %s", to)
        return

    resend.api_key = settings.RESEND_API_KEY
    try:
        response = resend.Emails.send(
            {
                "from": _SENDER,
                "to": to,
                "subject": subject,
                "html": html,
            }
        )
        logger.info("Email sent to %s (id=%s)", to, response.get("id"))
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)


def send_reset_email(to: str, reset_url: str) -> None:
    html = _reset_email_html(reset_url)
    _send_email(to, "Reset your Tayari password", html)


def send_verification_email(to: str, verify_url: str) -> None:
    html = _verify_email_html(verify_url)
    _send_email(to, "Verify your Tayari email address", html)


# ── HTML templates ──────────────────────────────────────────────────────────


def _base_html(body_content: str) -> str:
    body_style = (
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;"
        " margin: 0; padding: 0; background-color: #f4f4f5;"
    )
    card_style = "background: #ffffff; border-radius: 12px; padding: 40px 32px;"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="{body_style}">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding: 40px 16px;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0" style="{card_style}">
          {body_content}
          <tr>
            <td>
              <hr style="border: none; border-top: 1px solid #e4e4e7; margin: 0;" />
            </td>
          </tr>
          <tr>
            <td style="padding-top: 16px;">
              <p style="font-size: 12px; color: #a1a1aa; margin: 0;">
                Tayari AI — AI-powered interview preparation
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _reset_email_html(reset_url: str) -> str:
    btn_style = (
        "display: inline-block; background-color: #18181b; color: #ffffff;"
        " font-size: 14px; font-weight: 600; padding: 12px 32px;"
        " border-radius: 8px; text-decoration: none;"
    )
    body = f"""          <tr>
            <td align="center" style="padding-bottom: 24px;">
              <h1 style="font-size: 24px; font-weight: 700; color: #18181b; margin: 0;">Tayari AI</h1>
            </td>
          </tr>
          <tr>
            <td style="padding-bottom: 16px;">
              <p style="font-size: 16px; color: #18181b; margin: 0;">You requested a password reset.</p>
            </td>
          </tr>
          <tr>
            <td style="padding-bottom: 24px;">
              <p style="font-size: 14px; color: #71717a; margin: 0;">
                Click the button below to set a new password. This link expires in 1 hour.
              </p>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-bottom: 24px;">
              <a href="{reset_url}" style="{btn_style}">Reset Password</a>
            </td>
          </tr>
          <tr>
            <td style="padding-bottom: 16px;">
              <p style="font-size: 14px; color: #71717a; margin: 0;">
                If you didn't request this, you can safely ignore this email.
              </p>
            </td>
          </tr>"""
    return _base_html(body)


def _verify_email_html(verify_url: str) -> str:
    btn_style = (
        "display: inline-block; background-color: #18181b; color: #ffffff;"
        " font-size: 14px; font-weight: 600; padding: 12px 32px;"
        " border-radius: 8px; text-decoration: none;"
    )
    body = f"""          <tr>
            <td align="center" style="padding-bottom: 24px;">
              <h1 style="font-size: 24px; font-weight: 700; color: #18181b; margin: 0;">Tayari AI</h1>
            </td>
          </tr>
          <tr>
            <td style="padding-bottom: 16px;">
              <p style="font-size: 16px; color: #18181b; margin: 0;">Welcome to Tayari AI!</p>
            </td>
          </tr>
          <tr>
            <td style="padding-bottom: 24px;">
              <p style="font-size: 14px; color: #71717a; margin: 0;">
                Click the button below to verify your email address. This link expires in 24 hours.
              </p>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-bottom: 24px;">
              <a href="{verify_url}" style="{btn_style}">Verify Email</a>
            </td>
          </tr>
          <tr>
            <td style="padding-bottom: 16px;">
              <p style="font-size: 14px; color: #71717a; margin: 0;">
                If you didn't create an account, you can safely ignore this email.
              </p>
            </td>
          </tr>"""
    return _base_html(body)
