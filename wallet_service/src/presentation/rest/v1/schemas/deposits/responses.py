"""Deposit response schemas."""

import datetime

from pydantic import BaseModel, Field

from src.entities.deposit import DepositStatuses
from src.presentation.rest.v1.schemas.common import MoneyOut


__all__ = ('DepositResponseSchema',)


class DepositResponseSchema(BaseModel):
    """Response schema describing a deposit.

    Attributes:
        deposit_id: Deposit identifier
        status: Deposit status
        amount: Requested amount
        invoice_id: Provider invoice identifier
        pay_url: Provider payment page URL
        created_at: Creation time
    """

    deposit_id: str = Field(description='Deposit identifier')
    status: DepositStatuses = Field(description='Deposit status', examples=['pending'])
    amount: MoneyOut = Field(description='Requested amount')
    invoice_id: str | None = Field(description='Provider invoice identifier', examples=['inv_3f2a...'])
    pay_url: str | None = Field(description='Provider payment page URL')
    created_at: datetime.datetime = Field(description='Creation time')
