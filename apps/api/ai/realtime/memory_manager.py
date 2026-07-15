"""Conversation memory manager.

Maintains a sliding-window buffer of interview messages
for consumption by the AI provider.  Supports pause/resume
snapshots and transcript extraction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str
    timestamp_ms: int = 0


DEFAULT_MAX_TURNS = 20


@dataclass
class MemorySnapshot:
    messages: list[dict]
    turn_count: int
    token_estimate: int


class ConversationMemory:
    """Sliding-window conversation buffer.

    The system prompt and context messages are pinned (never evicted).
    Interview turns are kept up to ``max_turns``; older turns are dropped.
    """

    def __init__(
        self,
        system_prompt: str = "",
        context_messages: list[dict] | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
    ) -> None:
        self._system_prompt = system_prompt
        self._context: list[Message] = []
        self._turns: list[Message] = []
        self._max_turns = max_turns
        self._turn_count = 0

        if context_messages:
            for msg in context_messages:
                self._context.append(Message(role=msg["role"], content=msg["content"]))

    def append(self, role: str, content: str, timestamp_ms: int = 0) -> None:
        """Append a message and trim if over max_turns."""
        self._turns.append(Message(role=role, content=content, timestamp_ms=timestamp_ms))
        if role in {"user", "assistant"}:
            self._turn_count += 1
        self._trim()

    def _trim(self) -> None:
        """Keep only the most recent turns within max_turns."""
        assistant_turns = [m for m in self._turns if m.role == "assistant"]
        if len(assistant_turns) > self._max_turns:
            excess = len(assistant_turns) - self._max_turns
            # Count total messages to remove (user + assistant pairs)
            remove_count = 0
            seen_assistant = 0
            for msg in self._turns:
                if msg.role == "assistant":
                    seen_assistant += 1
                remove_count += 1
                if seen_assistant > excess:
                    break
            self._turns = self._turns[remove_count:]

    def get_all_messages(self) -> list[dict]:
        """Return the full message list for the AI provider."""
        result: list[dict] = []
        if self._system_prompt:
            result.append({"role": "system", "content": self._system_prompt})
        for msg in self._context:
            result.append({"role": msg.role, "content": msg.content})
        for msg in self._turns:
            result.append({"role": msg.role, "content": msg.content})
        return result

    def get_transcript(self) -> list[dict]:
        """Return only the turn-based transcript for persistence."""
        return [
            {"role": m.role, "content": m.content, "timestamp_ms": m.timestamp_ms}
            for m in self._turns
        ]

    def snapshot(self) -> MemorySnapshot:
        """Return a serializable snapshot for pause/reconnect."""
        return MemorySnapshot(
            messages=self.get_all_messages(),
            turn_count=self._turn_count,
            token_estimate=self._estimate_tokens(),
        )

    def restore(self, snapshot: MemorySnapshot) -> None:
        """Restore memory from a snapshot."""
        self._system_prompt = ""
        self._context = []
        self._turns = []
        self._turn_count = snapshot.turn_count

        for msg in snapshot.messages:
            if msg["role"] == "system":
                self._system_prompt = msg["content"]
            elif msg["role"] == "user" or msg["role"] == "assistant":
                self._turns.append(Message(role=msg["role"], content=msg["content"]))
            else:
                self._context.append(Message(role=msg["role"], content=msg["content"]))

    def _estimate_tokens(self) -> int:
        """Rough token estimate (4 chars ≈ 1 token)."""
        total_chars = len(self._system_prompt)
        for msg in self._context:
            total_chars += len(msg.content)
        for msg in self._turns:
            total_chars += len(msg.content)
        return total_chars // 4

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def message_count(self) -> int:
        return len(self._turns)
