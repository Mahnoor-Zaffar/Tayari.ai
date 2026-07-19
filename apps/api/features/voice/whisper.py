"""Whisper transcription service — forwards audio to the configured Whisper endpoint."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import httpx

from core.config import settings

log = logging.getLogger("voice.whisper")


class TranscriptionError(Exception):
    """Raised when the Whisper API call fails."""


def _transcribe_url() -> str:
    """Build the transcriptions endpoint from the Whisper base URL."""
    base = settings.WHISPER_BASE_URL.rstrip("/")
    return f"{base}/audio/transcriptions"


async def transcribe_audio(
    audio_bytes: bytes,
    *,
    filename: str = "audio.webm",
    language: str | None = None,
    prompt: str | None = None,
    model: str | None = None,
) -> dict:
    """Send audio bytes to the Whisper endpoint and return the result.

    Returns:
        {"text": str, "language": str, "duration_ms": int}
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise TranscriptionError("OPENAI_API_KEY is not configured")

    effective_model = model or "whisper-1"
    effective_language = language or settings.WHISPER_LANGUAGE
    effective_prompt = prompt or settings.WHISPER_PROMPT

    # Write audio to a temp file so we can send it as multipart/form-data
    suffix = Path(filename).suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(tmp_path, "rb") as f:
                files = {"file": (filename, f, "audio/webm")}
                data = {
                    "model": effective_model,
                    "language": effective_language,
                    "prompt": effective_prompt,
                }
                headers = {
                    "Authorization": f"Bearer {api_key}",
                }

                resp = await client.post(
                    _transcribe_url(),
                    headers=headers,
                    files=files,
                    data=data,
                )

            if resp.status_code != 200:
                body = resp.text[:500]
                log.error("Whisper API error: %s %s", resp.status_code, body)
                raise TranscriptionError(f"Whisper API returned {resp.status_code}: {body}")

            result = resp.json()
            text = result.get("text", "")
            lang = result.get("language", effective_language)
            usage = result.get("usage", {})
            duration_seconds = usage.get("seconds", 0)
            duration_ms = int(duration_seconds * 1000) if duration_seconds else 0

            log.info(
                "Transcription complete: %d chars, lang=%s, duration=%ds",
                len(text),
                lang,
                duration_seconds,
            )

            return {
                "text": text.strip(),
                "language": lang,
                "duration_ms": duration_ms,
            }

    except httpx.HTTPError as exc:
        log.error("HTTP error calling Whisper: %s", exc)
        raise TranscriptionError(f"Failed to reach Whisper API: {exc}") from exc
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass
