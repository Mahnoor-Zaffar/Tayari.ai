from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIResponse:
    content: str
    model: str
    usage: dict | None = None
    latency_ms: int = 0


class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], system_prompt: str | None = None, max_tokens: int = 1000) -> AIResponse:
        pass

    @abstractmethod
    async def chat_stream(self, messages: list[dict], system_prompt: str | None = None):
        pass

    @abstractmethod
    async def structured_output(self, messages: list[dict], response_model: type, system_prompt: str | None = None) -> dict:
        pass
