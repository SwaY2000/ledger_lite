"""Invoice response schemas."""

from pydantic import BaseModel, Field

from src.entities.invoice import InvoiceEntity, InvoiceStatuses
from src.presentation.rest.schemas.common import MoneyOut


__all__ = (
    'CreateInvoiceResponseSchema',
    'InvoiceResponseSchema',
    'DeliverySchema',
    'SimulateInvoiceResponseSchema',
)


class CreateInvoiceResponseSchema(BaseModel):
    """Response schema for invoice creation."""

    invoice_id: str
    status: InvoiceStatuses
    pay_url: str


class InvoiceResponseSchema(BaseModel):
    """Response schema describing an invoice."""

    invoice_id: str
    status: InvoiceStatuses
    amount: MoneyOut
    paid_amount: MoneyOut
    currency: str
    external_id: str

    @classmethod
    def from_entity(cls, invoice: InvoiceEntity) -> 'InvoiceResponseSchema':
        """Build the schema from an invoice entity."""
        return cls(
            invoice_id=invoice.ID,
            status=invoice.status,
            amount=invoice.amount,
            paid_amount=invoice.paid_amount,
            currency=invoice.currency,
            external_id=invoice.external_id,
        )


class DeliverySchema(BaseModel):
    """Result of one webhook delivery attempt."""

    status_code: int | None = Field(description='Receiver HTTP status, null on transport error')
    error: str | None = Field(description='Transport error')


class SimulateInvoiceResponseSchema(InvoiceResponseSchema):
    """Response schema for payment simulation."""

    event_id: str
    deliveries: list[DeliverySchema]
