"""Test doubles."""

from decimal import Decimal
from uuid import uuid4

from src.errors import BaseError
from src.services.payment_provider import ProviderInvoice, ProviderInvoiceStatuses


class FakePaymentProvider:
    """In-memory implementation of IPaymentProviderService."""

    def __init__(self) -> None:
        self.invoices: dict[str, ProviderInvoice] = {}
        self.error: BaseError | None = None

    async def create_invoice(self, amount: Decimal, external_id: str, callback_url: str) -> ProviderInvoice:
        if self.error:
            raise self.error
        invoice_id = f'inv_{uuid4().hex}'
        invoice = ProviderInvoice(
            invoice_id=invoice_id,
            status=ProviderInvoiceStatuses.PENDING,
            pay_url=f'http://provider.test/pay/{invoice_id}',
        )
        self.invoices[invoice_id] = invoice
        return invoice

    async def get_invoice(self, invoice_id: str) -> ProviderInvoice | None:
        if self.error:
            raise self.error
        return self.invoices.get(invoice_id)

    def set_status(self, invoice_id: str, status: ProviderInvoiceStatuses, paid_amount: str | None = None) -> None:
        invoice = self.invoices[invoice_id]
        invoice.status = status
        invoice.paid_amount = Decimal(paid_amount) if paid_amount is not None else None
