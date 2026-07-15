"""Tests for the conversation memory manager."""

from __future__ import annotations

from ai.realtime.memory_manager import ConversationMemory, MemorySnapshot


class TestConversationMemory:
    def test_append_system_prompt(self):
        memory = ConversationMemory(system_prompt="You are an interviewer.")
        messages = memory.get_all_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are an interviewer."

    def test_append_turns(self):
        memory = ConversationMemory(system_prompt="System prompt")
        memory.append("assistant", "Hello, welcome to the interview.")
        memory.append("user", "Thank you!")
        messages = memory.get_all_messages()
        assert len(messages) == 3  # system + assistant + user

    def test_turn_count_tracks_user_and_assistant(self):
        memory = ConversationMemory()
        assert memory.turn_count == 0
        memory.append("assistant", "Question 1")
        assert memory.turn_count == 1
        memory.append("user", "Answer 1")
        assert memory.turn_count == 2
        memory.append("system", "Some context")
        assert memory.turn_count == 2  # system messages don't count

    def test_sliding_window_trims_excess_turns(self):
        memory = ConversationMemory(max_turns=2)
        for i in range(5):
            memory.append("assistant", f"Question {i}")
            memory.append("user", f"Answer {i}")
        # After 10 messages (5 pairs), should keep only last 4 turns (2 pairs)
        messages = memory.get_all_messages()
        assert "Question 0" not in " ".join(m["content"] for m in messages)

    def test_snapshot_and_restore(self):
        memory = ConversationMemory(system_prompt="System")
        memory.append("assistant", "Hello")
        memory.append("user", "Hi")
        snapshot = memory.snapshot()
        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.turn_count == 2

        new_memory = ConversationMemory()
        new_memory.restore(snapshot)
        assert new_memory.turn_count == 2
        restored = new_memory.get_all_messages()
        assert any("Hello" in m["content"] for m in restored)
        assert any("Hi" in m["content"] for m in restored)

    def test_context_messages_are_pinned(self):
        context = [{"role": "user", "content": "Context message"}]
        memory = ConversationMemory(context_messages=context, max_turns=1)
        for i in range(10):
            memory.append("assistant", f"Q{i}")
            memory.append("user", f"A{i}")
        messages = memory.get_all_messages()
        # Context message should still be present after trimming
        assert any("Context message" in m["content"] for m in messages)

    def test_estimate_tokens(self):
        memory = ConversationMemory(system_prompt="Hello " * 100)
        estimate = memory._estimate_tokens()
        assert estimate > 0
        assert isinstance(estimate, int)

    def test_get_transcript_returns_only_turns(self):
        memory = ConversationMemory(system_prompt="System")
        memory.append("user", "User text")
        memory.append("assistant", "AI text")
        transcript = memory.get_transcript()
        assert all("system" not in seg["role"] for seg in transcript)
        assert len(transcript) == 2
