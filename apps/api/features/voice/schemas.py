"""Pydantic schemas for the voice feature.

REST request/response models for the TTS bridge that turns AI questions
into spoken audio served to the interview client.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """POST /voice/tts body — text to synthesize into speech."""

    text: str = Field(min_length=1, max_length=5000)
    voice: str | None = None
    session_id: str | None = None
    interview_id: str | None = None
