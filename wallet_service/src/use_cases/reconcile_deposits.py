"""Use case for reconciling pending deposits with the provider."""

import datetime
import logging

from src.entities.base import utc_now
from src.errors import BaseError
from src.repositories.interfaces import IUnitOfWork
from src.services.deposit_settlement import IDepositSettlementService, SettlementOutcomes
from src.services.payment_provider import IPaymentProviderService

from .dtos import ReconcileDepositsInput, ReconcileDepositsOutput


__all__ = ('ReconcileDepositsUseCase',)

logger = logging.getLogger(__name__)


class ReconcileDepositsUseCase:
    """Use case closing deposits whose webhook was lost.

    For every deposit pending longer than the threshold, the invoice state is
    fetched from the provider (outside of any transaction) and applied with
    the same settlement rules as the webhook, each deposit in its own
    transaction under a row lock. A webhook racing with reconciliation is
    harmless: whichever comes second sees a closed deposit and does nothing.
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        payment_provider_service: IPaymentProviderService,
        deposit_settlement_service: IDepositSettlementService,
    ) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow
        self._payment_provider_service = payment_provider_service
        self._settle = deposit_settlement_service

    async def __call__(self, request: ReconcileDepositsInput) -> ReconcileDepositsOutput:
        """Reconcile stale pending deposits.

        Args:
            request: Input DTO with age threshold and batch size

        Returns:
            Reconciliation statistics
        """
        older_than = utc_now() - datetime.timedelta(minutes=request.older_than_minutes)
        async with self._uow:
            deposit_ids = await self._uow.deposits.list_pending_ids_older_than(older_than, request.limit)

        output = ReconcileDepositsOutput()
        for deposit_id in deposit_ids:
            try:
                outcome = await self._reconcile_one(deposit_id)
            except BaseError as e:
                logger.warning(f'Failed to reconcile deposit {deposit_id}: {e.error_code}')
                output.errors[deposit_id] = e.error_code
                continue

            output.checked += 1
            if outcome is SettlementOutcomes.APPLIED:
                output.settled += 1
            elif outcome is SettlementOutcomes.STILL_PENDING:
                output.still_pending += 1

        return output

    async def _reconcile_one(self, deposit_id: str) -> SettlementOutcomes:
        """Fetch the invoice state and apply it to one deposit."""
        async with self._uow:
            deposit = await self._uow.deposits.get_by_id(deposit_id)
        if deposit is None or deposit.invoice_id is None or deposit.is_final:
            return SettlementOutcomes.ALREADY_CLOSED

        invoice = await self._payment_provider_service.get_invoice(deposit.invoice_id)
        if invoice is None:
            logger.warning(f'Invoice {deposit.invoice_id} of deposit {deposit_id} is unknown to the provider')
            return SettlementOutcomes.STILL_PENDING

        async with self._uow:
            locked = await self._uow.deposits.get_by_invoice_id_for_update(deposit.invoice_id)
            if locked is None:
                return SettlementOutcomes.ALREADY_CLOSED
            outcome = await self._settle(self._uow, locked, invoice.status, invoice.paid_amount)
            await self._uow.commit()

        logger.info(f'Reconciled deposit {deposit_id}: {outcome}')
        return outcome
