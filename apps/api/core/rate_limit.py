import time
from collections import defaultdict


class InMemoryRateLimiter:
    def __init__(self):
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds
        self._buckets[key] = [t for t in self._buckets[key] if t > window_start]
        if len(self._buckets[key]) >= max_requests:
            return False
        self._buckets[key].append(now)
        return True


rate_limiter = InMemoryRateLimiter()
