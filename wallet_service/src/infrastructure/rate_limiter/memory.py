"""In-memory sliding window rate limiter.

Suitable for a single-process deployment. With several replicas the limit
would be enforced per process; the ``IRateLimiter`` protocol allows swapping
in a Redis-based implementation without touching the presentation layer.
"""

import asyncio
import math
import time

from collections import deque
from collections.abc import Callable

from .base import RateLimitResult


__all__ = ('InMemoryRateLimiter',)


class InMemoryRateLimiter:
    """Sliding window log rate limiter stored in process memory."""

    def __init__(self, limit: int, window_seconds: int = 60, clock: Callable[[], float] = time.monotonic) -> None:
        """Initialize the limiter.

        Args:
            limit: Maximum number of requests per window
            window_seconds: Window length in seconds
            clock: Monotonic time source (injectable for tests)
        """
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def hit(self, key: str) -> RateLimitResult:
        """Register a request for the key and check the limit."""
        async with self._lock:
            now = self._clock()
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - self._window:
                hits.popleft()

            if len(hits) >= self._limit:
                retry_after = max(1, math.ceil(hits[0] + self._window - now))
                return RateLimitResult(allowed=False, retry_after=retry_after)

            hits.append(now)
            return RateLimitResult(allowed=True)

    def reset(self) -> None:
        """Forget all registered requests."""
        self._hits.clear()
