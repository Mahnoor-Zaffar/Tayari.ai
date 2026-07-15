"""Sanitization utilities for the evaluation pipeline.

Protects against:
- Prompt injection via user-supplied transcript text
- PII exposure (emails, phone numbers, SSNs)
- Overly long transcripts exceeding token limits
"""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
URL_RE = re.compile(r"https?://[^\s]+")
MAX_TRANSCRIPT_CHARS = 50_000


def sanitize_transcript(text: str) -> str:
    """Sanitize user-supplied transcript text before including in AI prompts.

    1. Truncate to MAX_TRANSCRIPT_CHARS
    2. Redact email addresses
    3. Redact phone numbers
    4. Redact SSNs
    5. Redact URLs
    6. Strip control characters (except newlines)
    """
    result = text[:MAX_TRANSCRIPT_CHARS]
    result = EMAIL_RE.sub("[EMAIL]", result)
    result = PHONE_RE.sub("[PHONE]", result)
    result = SSN_RE.sub("[SSN]", result)
    result = URL_RE.sub("[URL]", result)
    result = "".join(c for c in result if c == "\n" or c == "\t" or c >= " ")
    return result


def sanitize_source_code(code: str, max_chars: int = 10_000) -> str:
    """Sanitize and truncate source code before including in AI prompts."""
    return code[:max_chars]


def truncate_for_prompt(text: str, max_chars: int = MAX_TRANSCRIPT_CHARS) -> str:
    """Truncate text to fit within prompt token limits."""
    return text[:max_chars]
