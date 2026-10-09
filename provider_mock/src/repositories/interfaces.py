"""Repository interfaces."""

from typing import Protocol

from src.entities.invoice import InvoiceEntity


__all__ = ('IInvoiceRepository',)


class IInvoiceRepository(Protocol):
    """Repository interface for invoices."""

    async def save(self, invoice: InvoiceEntity) -> InvoiceEntity:
        """Create or replace an invoice."""

    async def get_by_id(self, invoice_id: str) -> InvoiceEntity | None:
        """Retrieve an invoice by its identifier."""
