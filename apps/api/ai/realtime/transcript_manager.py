"""Transcript manager.

Records structured transcript segments during the interview
and produces the final transcript for persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TranscriptSegment:
    speaker: str  # "ai" | "user"
    text: str
    timestamp_ms: int = 0
    is_final: bool = True
    metadata: dict[str, Any] | None = None


class TranscriptManager:
    """Manages the interview transcript.

    Accumulates segments during the session and produces
    the final ordered transcript for DB persistence.
    """

    def __init__(self) -> None:
        self._segments: list[TranscriptSegment] = []
        self._partial: str = ""  # Current partial (interim) text

    def append_partial(self, text: str, timestamp_ms: int = 0) -> None:
        """Update the current partial transcription."""
        self._partial = text

    def commit_partial(self, speaker: str, timestamp_ms: int = 0) -> TranscriptSegment:
        """Finalize the current partial into a committed segment."""
        segment = TranscriptSegment(
            speaker=speaker,
            text=self._partial,
            timestamp_ms=timestamp_ms,
            is_final=True,
        )
        self._segments.append(segment)
        self._partial = ""
        return segment

    def append_static(self, speaker: str, text: str, timestamp_ms: int = 0) -> TranscriptSegment:
        """Append a static (non-STT) segment, e.g. a question or hint."""
        segment = TranscriptSegment(
            speaker=speaker,
            text=text,
            timestamp_ms=timestamp_ms,
            is_final=True,
        )
        self._segments.append(segment)
        return segment

    def get_transcript(self) -> list[dict]:
        """Return all committed segments for persistence."""
        return [
            {
                "speaker": s.speaker,
                "text": s.text,
                "timestamp_ms": s.timestamp_ms,
                "is_final": s.is_final,
                "metadata": s.metadata,
            }
            for s in self._segments
        ]

    @property
    def full_text(self) -> str:
        """Return the full transcript as a single string."""
        return "\n".join(s.text for s in self._segments)

    @property
    def segment_count(self) -> int:
        return len(self._segments)

    def reset(self) -> None:
        self._segments.clear()
        self._partial = ""
