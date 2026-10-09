"""Use case for buying credits with the USD balance."""

from uuid import uuid4

from src.entities.base import utc_now
from src.entities.money import calculate_credits_price
from src.entities.transaction import TransactionEntity, TransactionTypes
from src.errors import AccountNotFoundError
from src.repositories.interfaces import IUnitOfWork

from .dtos import CreatePurchaseInput, PurchaseOutput


__all__ = ('CreatePurchaseUseCase',)


class CreatePurchaseUseCase:
    """Use case converting USD balance into credits at the current price tiers."""

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow

    async def __call__(self, request: CreatePurchaseInput) -> PurchaseOutput:
        """Buy credits.

        Args:
            request: Input DTO with account and number of credits

        Returns:
            Purchase result with updated balances

        Raises:
            InsufficientFundsError: Balance lower than the price (409)
        """
        price = calculate_credits_price(request.credits)

        async with self._uow:
            accounts = await self._uow.accounts.lock_many([request.account_id])
            account = accounts.get(request.account_id)
            if account is None:
                raise AccountNotFoundError

            account.debit(price)
            account.add_credits(request.credits)
            await self._uow.accounts.update(account)

            purchase_id = str(uuid4())
            created_at = utc_now()
            await self._uow.transactions.create(
                TransactionEntity(
                    account_id=account.ID,
                    type=TransactionTypes.PURCHASE,
                    amount_usd=-price,
                    credits=request.credits,
                    reference_id=purchase_id,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            )
            await self._uow.commit()

        return PurchaseOutput(
            purchase_id=purchase_id,
            credits=request.credits,
            price_usd=price,
            balance_usd=account.balance_usd,
            credits_balance=account.credits,
            created_at=created_at,
        )
