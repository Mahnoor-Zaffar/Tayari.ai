from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class AIResponse:
    content: str
    model: str
    usage: dict | None = None
    latency_ms: int = 0


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        model: str | None = None,
    ) -> AIResponse: ...

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream response chunks. Implementations are async generators."""

    @abstractmethod
    async def structured_output(
        self,
        messages: list[dict],
        response_model: type,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict: ...
