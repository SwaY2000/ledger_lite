"""Use case for creating accounts with API keys."""

from src.entities.account import AccountEntity
from src.repositories.interfaces import IUnitOfWork
from src.services.api_key import IApiKeyService

from .dtos import CreateAccountInput, CreateAccountOutput


__all__ = ('CreateAccountUseCase',)


class CreateAccountUseCase:
    """Use case for creating an account and issuing its API key."""

    def __init__(self, uow: IUnitOfWork, api_key_service: IApiKeyService) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow
        self._api_key_service = api_key_service

    async def __call__(self, request: CreateAccountInput) -> CreateAccountOutput:
        """Create an account with zero balances.

        Args:
            request: Input DTO with the account name

        Returns:
            Output DTO with the plain API key (shown only once)
        """
        api_key = self._api_key_service.generate()
        account = AccountEntity(name=request.name, api_key_hash=self._api_key_service.hash(api_key))

        async with self._uow:
            await self._uow.accounts.create(account)
            await self._uow.commit()

        return CreateAccountOutput(account_id=account.ID, name=account.name, api_key=api_key)
