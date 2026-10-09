"""API authentication module: ``Authorization: Bearer <PROVIDER_API_KEY>``."""

import hmac

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.errors import UnauthorizedError


__all__ = (
    'BEARER_AUTH',
    'is_valid_api_key_provided',
)


BEARER_AUTH = HTTPBearer(auto_error=False)


@inject
async def is_valid_api_key_provided(
    credentials: HTTPAuthorizationCredentials | None = Security(BEARER_AUTH),
    api_key: str = Depends(Provide['config.provider_api_key']),
) -> None:
    """Validate the bearer token.

    Raises:
        UnauthorizedError: 401 if the token is missing or invalid
    """
    if credentials is None or not hmac.compare_digest(credentials.credentials.encode(), api_key.encode()):
        raise UnauthorizedError
