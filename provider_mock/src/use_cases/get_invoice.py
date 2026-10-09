"""Use case for reading invoices."""

from src.entities.invoice import InvoiceEntity
from src.errors import InvoiceNotFoundError
from src.repositories.interfaces import IInvoiceRepository

from .dtos import GetInvoiceInput


__all__ = ('GetInvoiceUseCase',)


class GetInvoiceUseCase:
    """Use case returning the current invoice state."""

    def __init__(self, invoice_repository: IInvoiceRepository) -> None:
        """Initialize the use case with required dependencies."""
        self._invoice_repository = invoice_repository

    async def __call__(self, request: GetInvoiceInput) -> InvoiceEntity:
        """Return the invoice.

        Raises:
            InvoiceNotFoundError: If the invoice does not exist
        """
        invoice = await self._invoice_repository.get_by_id(request.invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError
        return invoice
