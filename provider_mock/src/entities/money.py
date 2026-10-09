"""Money helpers: amounts are JSON strings with at most two decimals."""

import re

from decimal import ROUND_HALF_UP, Decimal


__all__ = (
    'CENT',
    'parse_money',
    'format_money',
)


CENT = Decimal('0.01')

_MONEY_PATTERN = re.compile(r'^\d{1,10}(\.\d{1,2})?$')


def parse_money(value: object, *, allow_zero: bool = False) -> Decimal:
    """Parse a monetary amount received from JSON.

    Raises:
        ValueError: If the value is not a decimal string with at most two decimals
    """
    if not isinstance(value, str) or not _MONEY_PATTERN.fullmatch(value):
        raise ValueError('Amount must be a decimal string with at most 2 fractional digits, e.g. "10.00"')
    amount = Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)
    if not allow_zero and amount < CENT:
        raise ValueError(f'Amount must be at least {CENT}')
    return amount


def format_money(amount: Decimal) -> str:
    """Serialize an amount as a string with exactly two decimals."""
    return f'{amount.quantize(CENT, rounding=ROUND_HALF_UP):.2f}'
