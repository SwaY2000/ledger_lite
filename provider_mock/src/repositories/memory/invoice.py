"""In-memory invoice repository.

The provider mock keeps state in process memory: it is lost on restart,
which is acceptable for a test double.
"""

from src.entities.invoice import InvoiceEntity


__all__ = ('InMemoryInvoiceRepository',)


class InMemoryInvoiceRepository:
    """Invoice repository backed by a dict."""

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._invoices: dict[str, InvoiceEntity] = {}

    async def save(self, invoice: InvoiceEntity) -> InvoiceEntity:
        """Create or replace an invoice (a copy is stored to avoid aliasing)."""
        self._invoices[invoice.ID] = invoice.model_copy(deep=True)
        return invoice

    async def get_by_id(self, invoice_id: str) -> InvoiceEntity | None:
        """Retrieve a copy of an invoice by its identifier."""
        invoice = self._invoices.get(invoice_id)
        return invoice.model_copy(deep=True) if invoice else None
