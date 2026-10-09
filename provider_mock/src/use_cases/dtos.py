"""Data Transfer Objects (DTOs) for use case inputs and outputs."""

from dataclasses import dataclass, field
from decimal import Decimal

from src.entities.invoice import InvoiceEntity, InvoiceStatuses
from src.services.webhook_sender import DeliveryResult


__all__ = (
    'CreateInvoiceInput',
    'CreateInvoiceOutput',
    'GetInvoiceInput',
    'SimulateInvoiceInput',
    'SimulateInvoiceOutput',
)


@dataclass
class CreateInvoiceInput:
    """Input DTO for invoice creation."""

    amount: Decimal
    currency: str
    external_id: str
    callback_url: str


@dataclass
class CreateInvoiceOutput:
    """Output DTO for invoice creation."""

    invoice: InvoiceEntity
    pay_url: str


@dataclass
class GetInvoiceInput:
    """Input DTO for reading an invoice."""

    invoice_id: str


@dataclass
class SimulateInvoiceInput:
    """Input DTO for simulating a payment outcome.

    Attributes:
        invoice_id: Invoice identifier
        status: Final status to set
        paid_amount: Amount paid (defaults to the full amount for ``paid``)
        deliver_webhook: Whether to send the webhook
        duplicate: Whether to send the same webhook twice
    """

    invoice_id: str
    status: InvoiceStatuses
    paid_amount: Decimal | None = None
    deliver_webhook: bool = True
    duplicate: bool = False


@dataclass
class SimulateInvoiceOutput:
    """Output DTO for payment simulation."""

    invoice: InvoiceEntity
    event_id: str
    deliveries: list[DeliveryResult] = field(default_factory=list)
