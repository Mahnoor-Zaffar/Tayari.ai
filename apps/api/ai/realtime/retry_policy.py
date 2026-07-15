"""Failure recovery policies for the interview runtime.

Configurable retry strategies with exponential backoff,
jitter, and circuit breaker patterns for AI provider calls,
database operations, and WebSocket reconnections.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay_s: Base delay in seconds (doubles each attempt).
        max_delay_s: Maximum delay cap.
        jitter: If True, adds random jitter (±25%) to each delay.
        retryable_exceptions: Tuple of exception types that trigger retry.
    """

    max_retries: int = 3
    base_delay_s: float = 1.0
    max_delay_s: float = 30.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)


RETRY_POLICY_AI = RetryPolicy(
    max_retries=3,
    base_delay_s=1.0,
    max_delay_s=15.0,
    jitter=True,
    retryable_exceptions=(Exception,),
)

RETRY_POLICY_DB = RetryPolicy(
    max_retries=2,
    base_delay_s=0.5,
    max_delay_s=5.0,
    jitter=False,
    retryable_exceptions=(Exception,),
)


async def retry(
    policy: RetryPolicy,
    fn,
    *args: Any,
    on_retry: None = None,
    **kwargs: Any,
) -> Any:
    """Execute ``fn`` with retry logic defined by ``policy``.

    Raises the last exception if all retries are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(policy.max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except policy.retryable_exceptions as exc:
            last_exc = exc
            if attempt < policy.max_retries:
                delay = _calculate_delay(policy, attempt)
                logger.warning(
                    "Retry %d/%d for %s after %.1fs: %s",
                    attempt + 1, policy.max_retries, fn.__name__, delay, exc,
                )
                await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


def _calculate_delay(policy: RetryPolicy, attempt: int) -> float:
    delay = min(policy.base_delay_s * (2 ** attempt), policy.max_delay_s)
    if policy.jitter:
        delay *= 0.75 + random.random() * 0.5
    return delay


class CircuitBreakerState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker for AI provider calls.

    Prevents cascading failures by short-circuiting calls
    when the failure threshold is exceeded.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout_s: float = 30.0,
    ) -> None:
        self.name = name
        self._failure_threshold = failure_threshold
        self._reset_timeout_s = reset_timeout_s
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._last_success_time: float = 0.0

    @property
    def state(self) -> str:
        return self._state

    async def call(self, fn, *args: Any, **kwargs: Any) -> Any:
        """Execute fn if the circuit is closed/half-open.

        If the circuit is OPEN, raises CircuitBreakerError immediately.
        In HALF_OPEN state, allows one trial call.
        """
        if self._state == CircuitBreakerState.OPEN:
            if time.time() - self._last_failure_time > self._reset_timeout_s:
                self._state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerError(self.name, "Circuit is OPEN")

        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self._failure_count = 0
        self._last_success_time = time.time()
        self._state = CircuitBreakerState.CLOSED

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker %s OPEN after %d failures", self.name, self._failure_count)


class CircuitBreakerError(Exception):
    def __init__(self, name: str, message: str) -> None:
        self.name = name
        super().__init__(f"[{name}] {message}")
