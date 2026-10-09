"""Use case for creating deposits through the payment provider."""

import logging

from src.entities.deposit import DepositEntity
from src.errors import ProviderError, ProviderUnavailableError
from src.repositories.interfaces import IUnitOfWork
from src.services.payment_provider import IPaymentProviderService

from .dtos import CreateDepositInput, DepositOutput


__all__ = ('CreateDepositUseCase',)

logger = logging.getLogger(__name__)


class CreateDepositUseCase:
    """Use case creating a pending deposit and its provider invoice.

    The deposit is committed as ``pending`` before calling the provider, so a
    record exists even if the process crashes mid-request. The provider call
    happens outside of any database transaction to avoid holding connections
    and locks during network I/O.
    """

    def __init__(self, uow: IUnitOfWork, payment_provider_service: IPaymentProviderService, callback_url: str) -> None:
        """Initialize the use case with required dependencies.

        Args:
            uow: Unit of work
            payment_provider_service: Provider client
            callback_url: Public URL of the provider webhook endpoint
        """
        self._uow = uow
        self._payment_provider_service = payment_provider_service
        self._callback_url = callback_url

    async def __call__(self, request: CreateDepositInput) -> DepositOutput:
        """Create a deposit and an invoice at the provider.

        Args:
            request: Input DTO with account and amount

        Returns:
            Created deposit with ``pay_url``

        Raises:
            ProviderUnavailableError: Provider timed out or is unavailable (deposit marked failed)
            ProviderError: Provider rejected the invoice (deposit marked failed)
        """
        deposit = DepositEntity(account_id=request.account_id, amount=request.amount)

        async with self._uow:
            await self._uow.deposits.create(deposit)
            await self._uow.commit()

        try:
            invoice = await self._payment_provider_service.create_invoice(
                amount=deposit.amount,
                external_id=deposit.ID,
                callback_url=self._callback_url,
            )
        except (ProviderUnavailableError, ProviderError) as e:
            logger.warning(f'Failed to create invoice for deposit {deposit.ID}: {e.error_code}')
            # A timeout may still have created the invoice at the provider; the deposit is closed
            # and a late webhook for it is ignored (see README trade-offs).
            deposit.mark_failed()
            async with self._uow:
                await self._uow.deposits.update(deposit)
                await self._uow.commit()
            e.details.setdefault('deposit_id', deposit.ID)
            raise

        deposit.attach_invoice(invoice_id=invoice.invoice_id, pay_url=invoice.pay_url or '')
        async with self._uow:
            await self._uow.deposits.update(deposit)
            await self._uow.commit()

        return DepositOutput(
            deposit_id=deposit.ID,
            status=deposit.status,
            amount=deposit.amount,
            invoice_id=deposit.invoice_id,
            pay_url=deposit.pay_url,
            created_at=deposit.created_at,
        )
