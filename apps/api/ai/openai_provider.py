import time
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from ai.structured import parse_json_response
from core.config import settings

from .provider import AIProvider, AIResponse


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        model: str | None = None,
    ) -> AIResponse:
        full_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_messages.extend(messages)
        started = time.monotonic()
        try:
            response = await self.client.chat.completions.create(
                model=model or settings.AI_INTERVIEWER_MODEL,
                messages=full_messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
            )
        finally:
            latency_ms = int((time.monotonic() - started) * 1000)
        content = response.choices[0].message.content or ""
        return AIResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }
            if response.usage
            else None,
            latency_ms=latency_ms,
        )

    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        full_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_messages.extend(messages)
        stream = await self.client.chat.completions.create(
            model=model or settings.AI_INTERVIEWER_MODEL,
            messages=full_messages,  # type: ignore[arg-type]
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def structured_output(
        self,
        messages: list[dict],
        response_model: type,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict:
        full_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_messages.extend(messages)
        response = await self.client.chat.completions.create(  # type: ignore[call-overload]
            model=model or settings.AI_EVALUATOR_MODEL,
            messages=full_messages,
            response_format={"type": "json_object"},
        )
        result = parse_json_response(response_model, response.choices[0].message.content or "{}")
        if not isinstance(result, dict):
            raise ValueError(f"Expected a JSON object from structured output, got {type(result).__name__}")
        return result
