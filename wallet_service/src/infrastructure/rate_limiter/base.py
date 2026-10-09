"""Rate limiter interfaces."""

from dataclasses import dataclass
from typing import Protocol


__all__ = (
    'RateLimitResult',
    'IRateLimiter',
)


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of a rate limit check.

    Attributes:
        allowed: Whether the request may proceed
        retry_after: Seconds to wait before retrying (0 when allowed)
    """

    allowed: bool
    retry_after: int = 0


class IRateLimiter(Protocol):
    """Protocol for request rate limiters."""

    async def hit(self, key: str) -> RateLimitResult:
        """Register a request for the key and check the limit.

        Args:
            key: Identity being limited (e.g. account id)

        Returns:
            Rate limit outcome
        """
