"""Invoice entity module."""

from decimal import Decimal
from uuid import uuid4

from pydantic import Field

from src.entities.base import BaseEntity
from src.errors import InvoiceAlreadyFinalError, ValidationError

from .enums import InvoiceStatuses


__all__ = ('InvoiceEntity',)


class InvoiceEntity(BaseEntity):
    """Entity representing a payment invoice.

    Attributes:
        amount: Amount to pay
        currency: ISO currency code
        external_id: Merchant-side identifier (wallet deposit id)
        callback_url: URL receiving status change webhooks
        status: Current invoice status
        paid_amount: Amount actually paid
    """

    ID: str = Field(default_factory=lambda: f'inv_{uuid4().hex}', description='Invoice identifier')
    amount: Decimal = Field(..., description='Amount to pay')
    currency: str = Field(..., description='ISO currency code')
    external_id: str = Field(..., description='Merchant-side identifier')
    callback_url: str = Field(..., description='Webhook URL')
    status: InvoiceStatuses = Field(default=InvoiceStatuses.PENDING, description='Current invoice status')
    paid_amount: Decimal = Field(default=Decimal('0.00'), description='Amount actually paid')

    def change_status(self, status: InvoiceStatuses, paid_amount: Decimal | None) -> None:
        """Move the invoice to a final status.

        Args:
            status: New final status
            paid_amount: Amount paid (defaults to the full amount for PAID)

        Raises:
            InvoiceAlreadyFinalError: If the invoice is already final
            ValidationError: If the paid amount is inconsistent with the status
        """
        if self.status.is_final:
            raise InvoiceAlreadyFinalError(details={'status': self.status.value})

        if status is InvoiceStatuses.EXPIRED:
            paid_amount = Decimal('0.00')
        elif status is InvoiceStatuses.PAID:
            paid_amount = self.amount if paid_amount is None else paid_amount
        elif status is InvoiceStatuses.PARTIALLY_PAID and (paid_amount is None or not 0 < paid_amount < self.amount):
            raise ValidationError('partially_paid requires 0 < paid_amount < amount')

        self.status = status
        self.paid_amount = paid_amount or Decimal('0.00')
        self.touch()
