"""Use case for simulating payment outcomes."""

from uuid import uuid4

from src.entities.base import utc_now
from src.entities.money import format_money
from src.errors import InvoiceNotFoundError
from src.repositories.interfaces import IInvoiceRepository
from src.services.webhook_sender import IWebhookSenderService, WebhookEvent

from .dtos import SimulateInvoiceInput, SimulateInvoiceOutput


__all__ = ('SimulateInvoiceUseCase',)


class SimulateInvoiceUseCase:
    """Use case moving an invoice to a final status and notifying the merchant."""

    def __init__(self, invoice_repository: IInvoiceRepository, webhook_sender_service: IWebhookSenderService) -> None:
        """Initialize the use case with required dependencies."""
        self._invoice_repository = invoice_repository
        self._send_webhook = webhook_sender_service

    async def __call__(self, request: SimulateInvoiceInput) -> SimulateInvoiceOutput:
        """Change the invoice status and optionally deliver the webhook (once or twice).

        Raises:
            InvoiceNotFoundError: If the invoice does not exist
            InvoiceAlreadyFinalError: If the invoice is already final
            ValidationError: If the paid amount is inconsistent with the status
        """
        invoice = await self._invoice_repository.get_by_id(request.invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError

        invoice.change_status(request.status, request.paid_amount)
        await self._invoice_repository.save(invoice)

        event = WebhookEvent(
            event_id=f'evt_{uuid4().hex}',
            invoice_id=invoice.ID,
            status=invoice.status.value,
            paid_amount=format_money(invoice.paid_amount),
            occurred_at=utc_now(),
        )
        deliveries = []
        if request.deliver_webhook:
            deliveries = await self._send_webhook(invoice.callback_url, event, times=2 if request.duplicate else 1)

        return SimulateInvoiceOutput(invoice=invoice, event_id=event.event_id, deliveries=deliveries)
