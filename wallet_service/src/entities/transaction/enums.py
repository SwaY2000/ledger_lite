"""Transaction-related enumerations."""

from enum import StrEnum, auto


__all__ = ('TransactionTypes',)


class TransactionTypes(StrEnum):
    """Types of balance-changing operations recorded in the ledger."""

    DEPOSIT = auto()
    TRANSFER_IN = auto()
    TRANSFER_OUT = auto()
    PURCHASE = auto()
