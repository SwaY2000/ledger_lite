"""Transfer response schemas."""

import datetime

from pydantic import BaseModel, Field

from src.presentation.rest.v1.schemas.common import MoneyOut


__all__ = ('TransferResponseSchema',)


class TransferResponseSchema(BaseModel):
    """Response schema describing a completed transfer.

    Attributes:
        transfer_id: Transfer identifier
        from_account_id: Sender account
        to_account_id: Recipient account
        amount: Transferred amount
        balance_usd: Sender balance right after the transfer
        created_at: Transfer time
    """

    transfer_id: str = Field(description='Transfer identifier')
    from_account_id: str = Field(description='Sender account')
    to_account_id: str = Field(description='Recipient account')
    amount: MoneyOut = Field(description='Transferred amount')
    balance_usd: MoneyOut = Field(description='Sender balance right after the transfer')
    created_at: datetime.datetime = Field(description='Transfer time')
