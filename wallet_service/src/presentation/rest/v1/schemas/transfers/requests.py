"""Transfer request schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.presentation.rest.v1.schemas.common import MoneyAmount


__all__ = ('CreateTransferRequestSchema',)


class CreateTransferRequestSchema(BaseModel):
    """Request schema for a transfer.

    Attributes:
        to_account_id: Recipient account identifier
        amount: Amount to transfer (minimum "0.01")
    """

    model_config = ConfigDict(extra='forbid')

    to_account_id: UUID = Field(description='Recipient account identifier')
    amount: MoneyAmount = Field(description='Amount to transfer, minimum "0.01"')
