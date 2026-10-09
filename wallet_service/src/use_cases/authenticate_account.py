"""Use case for API key authentication."""

from src.entities.account import AccountEntity
from src.errors import UnauthorizedError
from src.repositories.interfaces import IUnitOfWork
from src.services.api_key import IApiKeyService

from .dtos import AuthenticateAccountInput


__all__ = ('AuthenticateAccountUseCase',)


class AuthenticateAccountUseCase:
    """Use case resolving the account that owns an API key."""

    def __init__(self, uow: IUnitOfWork, api_key_service: IApiKeyService) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow
        self._api_key_service = api_key_service

    async def __call__(self, request: AuthenticateAccountInput) -> AccountEntity:
        """Find the account by the hash of the provided API key.

        Args:
            request: Input DTO with the plain API key

        Returns:
            Authenticated account

        Raises:
            UnauthorizedError: If the key is missing or unknown
        """
        if not request.api_key:
            raise UnauthorizedError

        async with self._uow:
            account = await self._uow.accounts.get_by_api_key_hash(self._api_key_service.hash(request.api_key))

        if account is None:
            raise UnauthorizedError
        return account
