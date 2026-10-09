"""Sliding window rate limiter."""

from src.infrastructure.rate_limiter import InMemoryRateLimiter


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


async def test_limits_requests_within_window_and_recovers() -> None:
    clock = Clock()
    limiter = InMemoryRateLimiter(limit=30, window_seconds=60, clock=clock)

    results = [await limiter.hit('key') for _ in range(30)]
    clock.now += 20
    blocked = await limiter.hit('key')
    other_key = await limiter.hit('other')
    clock.now += 40
    recovered = await limiter.hit('key')

    assert all(r.allowed for r in results)
    assert not blocked.allowed
    assert blocked.retry_after == 40
    assert other_key.allowed
    assert recovered.allowed
