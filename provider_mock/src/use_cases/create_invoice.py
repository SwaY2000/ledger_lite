"""Use case for creating invoices."""

from src.entities.invoice import InvoiceEntity
from src.repositories.interfaces import IInvoiceRepository

from .dtos import CreateInvoiceInput, CreateInvoiceOutput


__all__ = ('CreateInvoiceUseCase',)


class CreateInvoiceUseCase:
    """Use case creating a pending invoice."""

    def __init__(self, invoice_repository: IInvoiceRepository, public_url: str) -> None:
        """Initialize the use case with required dependencies."""
        self._invoice_repository = invoice_repository
        self._public_url = public_url.rstrip('/')

    async def __call__(self, request: CreateInvoiceInput) -> CreateInvoiceOutput:
        """Create a pending invoice and return its payment URL."""
        invoice = InvoiceEntity(
            amount=request.amount,
            currency=request.currency,
            external_id=request.external_id,
            callback_url=request.callback_url,
        )
        await self._invoice_repository.save(invoice)
        return CreateInvoiceOutput(invoice=invoice, pay_url=f'{self._public_url}/pay/{invoice.ID}')
