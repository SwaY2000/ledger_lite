"""Deposit-related enumerations."""

from enum import StrEnum, auto


__all__ = ('DepositStatuses',)


class DepositStatuses(StrEnum):
    """Status values for the deposit lifecycle.

    PENDING is the only non-final status. PAID, PARTIALLY_PAID and EXPIRED
    mirror the final provider invoice statuses; FAILED means the invoice could
    not be created at the provider at all.
    """

    PENDING = auto()
    PAID = auto()
    PARTIALLY_PAID = auto()
    EXPIRED = auto()
    FAILED = auto()

    @property
    def is_final(self) -> bool:
        """Whether no further state transitions are allowed."""
        return self is not DepositStatuses.PENDING
