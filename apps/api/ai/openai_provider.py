import json

from openai import AsyncOpenAI

from core.config import settings

from .provider import AIProvider, AIResponse


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def chat(self, messages, system_prompt=None, max_tokens=1000):
        full_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_messages.extend(messages)
        response = await self.client.chat.completions.create(
            model=settings.AI_INTERVIEWER_MODEL,
            messages=full_messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return AIResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            } if response.usage else None,
        )

    async def chat_stream(self, messages, system_prompt=None):
        full_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_messages.extend(messages)
        stream = await self.client.chat.completions.create(
            model=settings.AI_INTERVIEWER_MODEL,
            messages=full_messages,  # type: ignore[arg-type]
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def structured_output(self, messages, response_model, system_prompt=None):
        full_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        full_messages.extend(messages)
        response = await self.client.chat.completions.create(  # type: ignore[call-overload]
            model=settings.AI_EVALUATOR_MODEL,
            messages=full_messages,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
