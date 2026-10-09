"""Payment provider enumerations."""

from enum import StrEnum, auto


__all__ = ('ProviderInvoiceStatuses',)


class ProviderInvoiceStatuses(StrEnum):
    """Invoice statuses reported by the payment provider.

    PAID, PARTIALLY_PAID and EXPIRED are final at the provider side.
    """

    PENDING = auto()
    PAID = auto()
    PARTIALLY_PAID = auto()
    EXPIRED = auto()
