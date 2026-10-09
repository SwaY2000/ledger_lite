"""Deposit request schemas."""

from pydantic import BaseModel, ConfigDict, Field

from src.presentation.rest.v1.schemas.common import MoneyAmount


__all__ = ('CreateDepositRequestSchema',)


class CreateDepositRequestSchema(BaseModel):
    """Request schema for deposit creation.

    Attributes:
        amount: Amount to deposit as a decimal string
    """

    model_config = ConfigDict(extra='forbid')

    amount: MoneyAmount = Field(description='Amount to deposit, e.g. "10.00"')
