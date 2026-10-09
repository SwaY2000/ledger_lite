"""Data structures exchanged with the payment provider."""

import datetime

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.entities.money import parse_money

from .enums import ProviderInvoiceStatuses


__all__ = (
    'ProviderInvoice',
    'ProviderWebhookEvent',
)


@dataclass
class ProviderInvoice:
    """Invoice state returned by the provider API.

    Attributes:
        invoice_id: Provider invoice identifier
        status: Current invoice status
        paid_amount: Amount actually paid (None while nothing is paid)
        pay_url: Payment page URL (only returned on creation)
    """

    invoice_id: str
    status: ProviderInvoiceStatuses
    paid_amount: Decimal | None = None
    pay_url: str | None = None


class ProviderWebhookEvent(BaseModel):
    """Webhook payload sent by the provider after an invoice status change.

    Parsed only after the signature has been verified.
    """

    event_id: str = Field(..., min_length=1, max_length=64, description='Provider event identifier')
    invoice_id: str = Field(..., min_length=1, max_length=64, description='Provider invoice identifier')
    status: ProviderInvoiceStatuses = Field(..., description='New invoice status')
    paid_amount: Decimal | None = Field(default=None, description='Amount actually paid')
    occurred_at: datetime.datetime | None = Field(default=None, description='Time of the status change')

    @field_validator('paid_amount', mode='before')
    @classmethod
    def _validate_paid_amount(cls, value: Any) -> Decimal | None:
        """Accept only string amounts with at most two decimals."""
        if value is None:
            return None
        return parse_money(value, allow_zero=True)
