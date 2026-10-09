"""Deposit settlement service.

Applies a final provider invoice status to a deposit. It is shared by the
webhook use case and the reconciliation use case, so both paths credit money
with exactly the same rules. The caller must have locked the deposit row in
the given unit of work.
"""

from decimal import Decimal
from enum import StrEnum, auto
from typing import Protocol

from src.entities.deposit import DepositEntity, DepositStatuses
from src.entities.transaction import TransactionEntity, TransactionTypes
from src.errors import AccountNotFoundError, ValidationError
from src.repositories.interfaces import IUnitOfWork
from src.services.payment_provider import ProviderInvoiceStatuses


__all__ = (
    'SettlementOutcomes',
    'IDepositSettlementService',
    'DepositSettlementService',
)


class SettlementOutcomes(StrEnum):
    """Result of applying a provider status to a deposit."""

    APPLIED = auto()
    ALREADY_CLOSED = auto()
    STILL_PENDING = auto()


class IDepositSettlementService(Protocol):
    """Protocol for the deposit settlement service."""

    async def __call__(
        self,
        uow: IUnitOfWork,
        deposit: DepositEntity,
        status: ProviderInvoiceStatuses,
        paid_amount: Decimal | None,
    ) -> SettlementOutcomes:
        """Apply a provider invoice status to a locked deposit."""


class DepositSettlementService:
    """Deposit settlement implementation."""

    async def __call__(
        self,
        uow: IUnitOfWork,
        deposit: DepositEntity,
        status: ProviderInvoiceStatuses,
        paid_amount: Decimal | None,
    ) -> SettlementOutcomes:
        """Apply a provider invoice status to a locked deposit.

        Rules:
            - a closed deposit never changes again (late or repeated events are ignored);
            - ``pending`` keeps the deposit open;
            - ``expired`` closes the deposit without crediting;
            - ``paid``/``partially_paid`` credit ``paid_amount - fee`` to the account.

        Args:
            uow: Active unit of work holding the deposit lock
            deposit: Deposit locked with ``SELECT ... FOR UPDATE``
            status: Invoice status reported by the provider
            paid_amount: Amount actually paid

        Returns:
            Settlement outcome

        Raises:
            ValidationError: If a partial payment has no paid amount
        """
        if deposit.is_final:
            return SettlementOutcomes.ALREADY_CLOSED

        if status is ProviderInvoiceStatuses.PENDING:
            return SettlementOutcomes.STILL_PENDING

        if status is ProviderInvoiceStatuses.EXPIRED:
            deposit.expire()
            await uow.deposits.update(deposit)
            return SettlementOutcomes.APPLIED

        if paid_amount is None:
            if status is ProviderInvoiceStatuses.PARTIALLY_PAID:
                raise ValidationError('paid_amount is required for partially_paid status')
            paid_amount = deposit.amount

        credited = deposit.settle_paid(DepositStatuses(status.value), paid_amount)
        await uow.deposits.update(deposit)

        if credited > 0:
            accounts = await uow.accounts.lock_many([deposit.account_id])
            account = accounts.get(deposit.account_id)
            if account is None:
                raise AccountNotFoundError

            account.credit(credited)
            await uow.accounts.update(account)
            await uow.transactions.create(
                TransactionEntity(
                    account_id=account.ID,
                    type=TransactionTypes.DEPOSIT,
                    amount_usd=credited,
                    reference_id=deposit.ID,
                ),
            )

        return SettlementOutcomes.APPLIED
