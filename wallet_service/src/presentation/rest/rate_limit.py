"""Rate limiting dependency.

Limits POST requests per API key (account). Applied to state-changing
client endpoints only; the provider webhook is intentionally not limited.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from src.entities.account import AccountEntity
from src.errors import RateLimitExceededError
from src.infrastructure.rate_limiter import IRateLimiter

from .auth import get_current_account


__all__ = ('enforce_rate_limit',)


@inject
async def enforce_rate_limit(
    account: AccountEntity = Depends(get_current_account),
    rate_limiter: IRateLimiter = Depends(Provide['rate_limiter']),
) -> None:
    """Reject the request with 429 if the account exceeded its limit.

    Args:
        account: Authenticated account (resolved once per request)
        rate_limiter: Injected rate limiter

    Raises:
        RateLimitExceededError: 429 with the Retry-After header
    """
    result = await rate_limiter.hit(account.ID)
    if not result.allowed:
        raise RateLimitExceededError(retry_after=result.retry_after)
