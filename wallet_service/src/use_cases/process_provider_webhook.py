"""Use case for processing payment provider webhooks."""

import logging

from typing import Literal

import pydantic

from src.entities.webhook_event import WebhookEventEntity
from src.errors import DepositNotFoundError, ValidationError
from src.repositories.interfaces import IUnitOfWork
from src.services.deposit_settlement import IDepositSettlementService, SettlementOutcomes
from src.services.payment_provider import ProviderWebhookEvent
from src.services.webhook_verifier import IWebhookSignatureVerifier

from .dtos import ProcessProviderWebhookInput, ProcessProviderWebhookOutput


__all__ = ('ProcessProviderWebhookUseCase',)

logger = logging.getLogger(__name__)


class ProcessProviderWebhookUseCase:
    """Use case applying a signed provider webhook to a deposit.

    Exactly-once crediting is guaranteed by two independent mechanisms in
    one transaction: the unique ``event_id`` (duplicates are no-ops) and the
    deposit row lock plus final-status check (late events are no-ops).
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        webhook_signature_verifier: IWebhookSignatureVerifier,
        deposit_settlement_service: IDepositSettlementService,
    ) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow
        self._verify_signature = webhook_signature_verifier
        self._settle = deposit_settlement_service

    async def __call__(self, request: ProcessProviderWebhookInput) -> ProcessProviderWebhookOutput:
        """Verify, deduplicate and apply a provider webhook.

        Args:
            request: Raw body and signature headers

        Returns:
            Processing result

        Raises:
            InvalidSignatureError: Signature missing, invalid or expired (401)
            ValidationError: Payload is malformed (422)
            DepositNotFoundError: Unknown invoice (404, nothing is stored so a retry can succeed)
        """
        self._verify_signature(request.raw_body, request.signature, request.timestamp)

        try:
            event = ProviderWebhookEvent.model_validate_json(request.raw_body)
        except pydantic.ValidationError as e:
            raise ValidationError(
                'Invalid webhook payload',
                details={'errors': e.errors(include_url=False, include_context=False, include_input=False)},
            ) from e

        async with self._uow:
            is_new = await self._uow.webhook_events.try_create(
                WebhookEventEntity(
                    event_id=event.event_id,
                    invoice_id=event.invoice_id,
                    status=event.status.value,
                    paid_amount=event.paid_amount,
                    occurred_at=event.occurred_at,
                ),
            )
            if not is_new:
                logger.info(f'Duplicate webhook event {event.event_id} ignored')
                return ProcessProviderWebhookOutput(result='duplicate')

            deposit = await self._uow.deposits.get_by_invoice_id_for_update(event.invoice_id)
            if deposit is None:
                raise DepositNotFoundError(details={'invoice_id': event.invoice_id})

            outcome = await self._settle(self._uow, deposit, event.status, event.paid_amount)
            await self._uow.commit()

        logger.info(f'Webhook {event.event_id} for deposit {deposit.ID}: {outcome}')
        result: Literal['processed', 'ignored'] = 'processed' if outcome is SettlementOutcomes.APPLIED else 'ignored'
        return ProcessProviderWebhookOutput(result=result, deposit_id=deposit.ID)
