"""API authentication module.

This module provides per-account API key authentication. The key is read
from the ``X-API-Key`` header, hashed and looked up; plain keys are never
stored.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Security
from fastapi.security.api_key import APIKeyHeader

from src.entities.account import AccountEntity
from src.use_cases.dtos import AuthenticateAccountInput
from src.use_cases.interfaces import IUseCase


__all__ = (
    'API_KEY_HEADER_AUTH',
    'get_current_account',
)


API_KEY_HEADER_AUTH = APIKeyHeader(
    name='X-API-Key',
    auto_error=False,
)


@inject
async def get_current_account(
    api_key_header: str | None = Security(API_KEY_HEADER_AUTH),
    uc: IUseCase[AuthenticateAccountInput, AccountEntity] = Depends(Provide['authenticate_account_use_case']),
) -> AccountEntity:
    """Resolve the account owning the provided API key.

    Args:
        api_key_header: API key from the X-API-Key header
        uc: Injected authentication use case

    Returns:
        Authenticated account

    Raises:
        UnauthorizedError: 401 if the API key is missing or invalid
    """
    return await uc(AuthenticateAccountInput(api_key=api_key_header))
