"""Ledger transaction entity module.

Every balance change is recorded as an immutable ledger row, which is
used for the operation history endpoint.
"""

from decimal import Decimal

from pydantic import Field

from src.entities.base import BaseEntity

from .enums import TransactionTypes


__all__ = ('TransactionEntity',)


class TransactionEntity(BaseEntity):
    """Entity representing a single ledger entry of an account.

    Attributes:
        account_id: Account whose balance changed
        type: Operation type
        amount_usd: Signed USD balance change (negative for debits)
        credits: Signed credits balance change
        reference_id: Identifier of the originating operation (deposit, transfer, purchase)
        counterparty_account_id: Other account of a transfer
    """

    account_id: str = Field(..., description='Account whose balance changed')
    type: TransactionTypes = Field(..., description='Operation type')
    amount_usd: Decimal = Field(..., description='Signed USD balance change')
    credits: int = Field(0, description='Signed credits balance change')
    reference_id: str | None = Field(None, description='Originating operation identifier')
    counterparty_account_id: str | None = Field(None, description='Other account of a transfer')
