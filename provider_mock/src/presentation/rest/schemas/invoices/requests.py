"""Invoice request schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from src.entities.invoice import InvoiceStatuses
from src.presentation.rest.schemas.common import MoneyAmount, PaidAmount


__all__ = (
    'CreateInvoiceRequestSchema',
    'SimulateInvoiceRequestSchema',
)


class CreateInvoiceRequestSchema(BaseModel):
    """Request schema for invoice creation."""

    amount: MoneyAmount = Field(description='Amount to pay')
    currency: Literal['USD'] = Field(description='Currency, only USD is supported')
    external_id: str = Field(min_length=1, max_length=64, description='Merchant-side identifier')
    callback_url: str = Field(min_length=1, max_length=2048, description='Webhook URL')


class SimulateInvoiceRequestSchema(BaseModel):
    """Request schema for payment simulation."""

    status: Literal[InvoiceStatuses.PAID, InvoiceStatuses.PARTIALLY_PAID, InvoiceStatuses.EXPIRED] = Field(
        description='Final status to set',
    )
    paid_amount: PaidAmount | None = Field(default=None, description='Amount paid; defaults to amount for paid')
    deliver_webhook: bool = Field(default=True, description='Send the webhook to callback_url')
    duplicate: bool = Field(default=False, description='Send the same webhook twice')
