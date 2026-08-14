"""Model Gateway — the single entry point for every AI call.

Implements the ``AIProvider`` interface so all existing consumers (interview
orchestrator, evaluation evaluators, code review) keep working unchanged.  The
gateway:

- Routes each task to the configured backend provider (OpenAI-compatible
  today; other backends plug in behind the same interface).
- Selects a model per task (cheap/fast vs. strong), overridable via config.
- Records usage telemetry (model, tokens, latency, cost, prompt version,
  success/failure) for observability.
"""

from __future__ import annotations

import logging
import time

from core.config import settings

from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider
from .provider import AIProvider, AIResponse
from .usage.recorder import (
    DEFAULT_PROMPT_VERSION,
    UsageRecord,
    UsageRecorder,
    estimate_cost_cents,
    get_usage_recorder,
)

logger = logging.getLogger(__name__)

TASK_CHAT = "chat"
TASK_STREAM = "stream"
TASK_STRUCTURED = "structured"

BACKEND_OPENAI = "openai"
BACKEND_MOCK = "mock"


class ModelGateway(AIProvider):
    """Routes AI calls to the configured backend and records usage."""

    def __init__(
        self,
        provider: AIProvider | None = None,
        recorder: UsageRecorder | None = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ) -> None:
        self._provider = provider
        self._recorder = recorder
        self._prompt_version = prompt_version

    def _backend(self) -> AIProvider:
        if self._provider is not None:
            return self._provider
        if settings.OPENAI_API_KEY:
            self._provider = OpenAIProvider()
        else:
            logger.warning("No OPENAI_API_KEY set — using MockProvider via ModelGateway")
            self._provider = MockProvider()
        return self._provider

    @property
    def provider_name(self) -> str:
        return BACKEND_OPENAI if settings.OPENAI_API_KEY else BACKEND_MOCK

    # ── task → model routing (additive; overrides in config win) ──────────

    def _chat_model(self) -> str:
        return settings.MODEL_GATEWAY_CHAT_MODEL or settings.AI_INTERVIEWER_MODEL

    def _structured_model(self) -> str:
        return settings.MODEL_GATEWAY_STRUCTURED_MODEL or settings.AI_EVALUATOR_MODEL

    # ── AIProvider interface ──────────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        model: str | None = None,
    ) -> AIResponse:
        requested_model = model or self._chat_model()
        started = time.monotonic()
        try:
            response = await self._backend().chat(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                model=requested_model,
            )
        except Exception as exc:
            self._record(
                task=TASK_CHAT,
                model=requested_model,
                latency_ms=(time.monotonic() - started) * 1000,
                is_error=True,
                error_message=str(exc),
            )
            raise
        self._record_usage_response(TASK_CHAT, requested_model, response, started)
        return response

    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
    ):
        requested_model = model or self._chat_model()
        started = time.monotonic()
        content_parts: list[str] = []
        try:
            async for chunk in self._backend().chat_stream(
                messages=messages,
                system_prompt=system_prompt,
                model=requested_model,
            ):
                if chunk:
                    content_parts.append(chunk)
                yield chunk
        except Exception as exc:
            self._record(
                task=TASK_STREAM,
                model=requested_model,
                latency_ms=(time.monotonic() - started) * 1000,
                is_error=True,
                error_message=str(exc),
            )
            raise
        self._record(
            task=TASK_STREAM,
            model=requested_model,
            latency_ms=(time.monotonic() - started) * 1000,
            completion_tokens=None,
            prompt_tokens=None,
        )

    async def structured_output(
        self,
        messages: list[dict],
        response_model: type,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict:
        requested_model = model or self._structured_model()
        started = time.monotonic()
        try:
            result = await self._backend().structured_output(
                messages=messages,
                response_model=response_model,
                system_prompt=system_prompt,
                model=requested_model,
            )
        except Exception as exc:
            self._record(
                task=TASK_STRUCTURED,
                model=requested_model,
                latency_ms=(time.monotonic() - started) * 1000,
                is_error=True,
                error_message=str(exc),
            )
            raise
        self._record(
            task=TASK_STRUCTURED,
            model=requested_model,
            latency_ms=(time.monotonic() - started) * 1000,
        )
        return result

    # ── recording helpers ─────────────────────────────────────────────────

    def _record_usage_response(self, task: str, model: str, response: AIResponse, started: float) -> None:
        usage = response.usage or {}
        self._record(
            task=task,
            model=response.model or model,
            latency_ms=(time.monotonic() - started) * 1000,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

    def _record(
        self,
        task: str,
        model: str,
        *,
        latency_ms: float,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        is_error: bool = False,
        error_message: str | None = None,
    ) -> None:
        recorder = self._recorder or get_usage_recorder()
        recorder.record_sync(
            _make_record(
                task=task,
                provider=self.provider_name,
                model=model,
                latency_ms=round(latency_ms, 1),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                is_error=is_error,
                error_message=error_message,
                prompt_version=self._prompt_version,
            )
        )


def _make_record(**kwargs: object) -> UsageRecord:
    record: UsageRecord = UsageRecord(**kwargs)  # type: ignore[arg-type]
    record.estimated_cost_cents = estimate_cost_cents(record.model, record.prompt_tokens, record.completion_tokens)
    return record


def get_model_gateway() -> ModelGateway:
    """Return the shared model gateway singleton."""
    global _gateway
    if _gateway is None:
        _gateway = ModelGateway()
    return _gateway


_gateway: ModelGateway | None = None
