"""Transcript Analyzer — extracts structured data from interview transcripts.

Parses raw transcript segments into analyzable turns, measures
response timing, and identifies code segments.
"""

from __future__ import annotations

from typing import Any


class TranscriptAnalyzer:
    """Analyzes interview transcripts for evaluation input.

    Produces:
    - Turn-by-turn breakdown (speaker, text, timing)
    - Response latency metrics
    - Total speaking time per participant
    - Code segment extraction (for coding interviews)
    """

    def analyze(self, transcript: list[dict]) -> dict[str, Any]:
        """Analyze a raw transcript and return structured metrics."""
        if not transcript:
            return self._empty_result()

        turns: list[dict] = []
        ai_turns = 0
        user_turns = 0
        ai_words = 0
        user_words = 0
        total_pause_ms = 0
        last_timestamp: int | None = None

        for entry in transcript:
            speaker = entry.get("speaker", entry.get("role", "unknown"))
            text = entry.get("text", entry.get("content", ""))
            ts = entry.get("timestamp_ms", 0)

            turn = {"speaker": speaker, "text": text, "timestamp_ms": ts}
            turns.append(turn)

            word_count = len(text.split())
            if speaker in ("ai", "assistant"):
                ai_turns += 1
                ai_words += word_count
            elif speaker in ("user", "candidate"):
                user_turns += 1
                user_words += word_count

            if last_timestamp is not None and ts > last_timestamp:
                pause = ts - last_timestamp
                if pause > 1000:  # Only count pauses > 1s
                    total_pause_ms += pause
            last_timestamp = ts

        return {
            "total_turns": len(turns),
            "ai_turns": ai_turns,
            "user_turns": user_turns,
            "ai_word_count": ai_words,
            "user_word_count": user_words,
            "total_words": ai_words + user_words,
            "total_pause_ms": total_pause_ms,
            "avg_response_ms": total_pause_ms / max(user_turns, 1),
            "turns": turns,
        }

    def format_for_prompt(self, transcript: list[dict]) -> str:
        """Format transcript as readable text for inclusion in an AI prompt."""
        analysis = self.analyze(transcript)
        lines: list[str] = []
        for turn in analysis["turns"]:
            speaker_label = "Interviewer" if turn["speaker"] in ("ai", "assistant") else "Candidate"
            lines.append(f"{speaker_label}: {turn['text']}")
        return "\n\n".join(lines)

    def _empty_result(self) -> dict[str, Any]:
        return {
            "total_turns": 0, "ai_turns": 0, "user_turns": 0,
            "ai_word_count": 0, "user_word_count": 0, "total_words": 0,
            "total_pause_ms": 0, "avg_response_ms": 0, "turns": [],
        }
