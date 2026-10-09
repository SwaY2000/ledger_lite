"""Transaction history response schemas."""

import datetime

from pydantic import BaseModel, Field

from src.entities.transaction import TransactionTypes
from src.presentation.rest.v1.schemas.common import MoneyOut


__all__ = (
    'TransactionItemSchema',
    'TransactionListResponseSchema',
)


class TransactionItemSchema(BaseModel):
    """Single ledger entry.

    Attributes:
        transaction_id: Ledger entry identifier
        type: Operation type
        amount_usd: Signed USD change (negative for debits)
        credits: Signed credits change
        reference_id: Originating deposit, transfer or purchase
        counterparty_account_id: Other account of a transfer
        created_at: Operation time
    """

    transaction_id: str = Field(description='Ledger entry identifier')
    type: TransactionTypes = Field(description='Operation type', examples=['transfer_out'])
    amount_usd: MoneyOut = Field(description='Signed USD change', examples=['-5.00'])
    credits: int = Field(description='Signed credits change', examples=[0])
    reference_id: str | None = Field(description='Originating deposit, transfer or purchase')
    counterparty_account_id: str | None = Field(description='Other account of a transfer')
    created_at: datetime.datetime = Field(description='Operation time')


class TransactionListResponseSchema(BaseModel):
    """Page of the operation history.

    Attributes:
        items: Ledger entries, newest first
        next_cursor: Cursor for the next page (null on the last page)
    """

    items: list[TransactionItemSchema]
    next_cursor: str | None = Field(description='Pass as ?cursor= to get the next page')
