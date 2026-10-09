"""Use case for reading account balances."""

from src.errors import AccountNotFoundError
from src.repositories.interfaces import IUnitOfWork

from .dtos import AccountOutput, GetAccountInput


__all__ = ('GetAccountUseCase',)


class GetAccountUseCase:
    """Use case returning the USD and credits balances of an account."""

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow

    async def __call__(self, request: GetAccountInput) -> AccountOutput:
        """Read the account balances.

        Args:
            request: Input DTO with the account identifier

        Returns:
            Account balances

        Raises:
            AccountNotFoundError: If the account does not exist
        """
        async with self._uow:
            account = await self._uow.accounts.get_by_id(request.account_id)

        if account is None:
            raise AccountNotFoundError
        return AccountOutput.from_entity(account)
