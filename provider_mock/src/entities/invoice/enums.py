"""Invoice-related enumerations."""

from enum import StrEnum, auto


__all__ = ('InvoiceStatuses',)


class InvoiceStatuses(StrEnum):
    """Invoice lifecycle statuses. Everything except PENDING is final."""

    PENDING = auto()
    PAID = auto()
    PARTIALLY_PAID = auto()
    EXPIRED = auto()

    @property
    def is_final(self) -> bool:
        """Whether no further status changes are allowed."""
        return self is not InvoiceStatuses.PENDING
