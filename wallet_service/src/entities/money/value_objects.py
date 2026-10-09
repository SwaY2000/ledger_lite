"""Money value objects and pricing rules.

All monetary amounts in the wallet service are ``Decimal`` values in USD
with cent precision. This module is the single place where rounding,
provider fee and credit pricing rules live, so every use case applies
exactly the same arithmetic.
"""

import re

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


__all__ = (
    'CENT',
    'PROVIDER_FEE_RATE',
    'CREDIT_BASE_PRICE',
    'CREDIT_DISCOUNT_TIERS',
    'MIN_TRANSFER_AMOUNT',
    'MAX_AMOUNT',
    'quantize_cents',
    'calculate_provider_fee',
    'calculate_net_deposit',
    'calculate_credits_price',
    'parse_money',
    'format_money',
)


CENT = Decimal('0.01')
"""Smallest monetary unit stored for USD balances."""

PROVIDER_FEE_RATE = Decimal('0.015')
"""Provider fee: 1.5% of the actually paid amount."""

CREDIT_BASE_PRICE = Decimal('0.10')
"""Base price of a single credit in USD."""

CREDIT_DISCOUNT_TIERS: tuple[tuple[int, Decimal], ...] = (
    (1000, Decimal('0.125')),
    (500, Decimal('0.05')),
)
"""Volume discounts as (min_credits, discount_rate), ordered from the largest threshold."""

MIN_TRANSFER_AMOUNT = CENT
"""Minimal transfer amount."""

MAX_AMOUNT = Decimal('9999999999.99')
"""Largest amount accepted by the API (fits NUMERIC(18, 2) with headroom)."""

_MONEY_PATTERN = re.compile(r'^\d{1,10}(\.\d{1,2})?$')


def quantize_cents(amount: Decimal) -> Decimal:
    """Round an amount to cents using ROUND_HALF_UP.

    Args:
        amount: Arbitrary precision decimal amount

    Returns:
        Amount rounded to two decimal places
    """
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_provider_fee(paid_amount: Decimal) -> Decimal:
    """Calculate the provider fee for an actually paid amount.

    Args:
        paid_amount: Amount paid by the user at the provider

    Returns:
        Fee rounded to cents with ROUND_HALF_UP

    Examples:
        10.00 -> 0.15, 0.99 -> 0.01, 33.33 -> 0.50
    """
    return quantize_cents(paid_amount * PROVIDER_FEE_RATE)


def calculate_net_deposit(paid_amount: Decimal) -> Decimal:
    """Calculate the amount credited to the balance: paid minus fee.

    Args:
        paid_amount: Amount paid by the user at the provider

    Returns:
        Net amount to credit, rounded to cents

    Examples:
        10.00 -> 9.85, 0.99 -> 0.98, 33.33 -> 32.83
    """
    paid = quantize_cents(paid_amount)
    return paid - calculate_provider_fee(paid)


def calculate_credits_price(credits: int) -> Decimal:
    """Calculate the USD price of a credits package.

    Base price is 0.10 USD per credit; 5% discount from 500 credits and
    12.5% discount from 1000 credits. The final price is rounded to cents
    with ROUND_HALF_UP.

    Args:
        credits: Number of credits to purchase (must be positive)

    Returns:
        Final price in USD

    Raises:
        ValueError: If credits is not a positive integer

    Examples:
        333 -> 33.30, 507 -> 48.17, 1005 -> 87.94
    """
    if credits <= 0:
        raise ValueError('Credits must be a positive integer')

    discount = next((rate for threshold, rate in CREDIT_DISCOUNT_TIERS if credits >= threshold), Decimal('0'))
    return quantize_cents(Decimal(credits) * CREDIT_BASE_PRICE * (Decimal('1') - discount))


def parse_money(value: object, *, allow_zero: bool = False) -> Decimal:
    """Parse a monetary amount received from JSON.

    Amounts must be JSON strings with at most two fractional digits
    (e.g. ``"10.00"``). Numbers are rejected to avoid binary float errors.

    Args:
        value: Raw JSON value
        allow_zero: Whether ``"0.00"`` is an acceptable amount

    Returns:
        Parsed amount quantized to cents

    Raises:
        ValueError: If the value is not a string, has more than two decimals,
            is negative, zero (unless allowed) or too large
    """
    if not isinstance(value, str):
        raise ValueError('Amount must be a JSON string, e.g. "10.00"')
    if not _MONEY_PATTERN.fullmatch(value):
        raise ValueError('Amount must be a non-negative decimal string with at most 2 fractional digits')

    try:
        amount = Decimal(value)
    except InvalidOperation as e:
        raise ValueError('Amount is not a valid decimal') from e

    if amount > MAX_AMOUNT:
        raise ValueError(f'Amount must not exceed {MAX_AMOUNT}')
    if not allow_zero and amount < CENT:
        raise ValueError(f'Amount must be at least {CENT}')

    return quantize_cents(amount)


def format_money(amount: Decimal) -> str:
    """Serialize an amount to a JSON string with exactly two decimals.

    Args:
        amount: Amount to serialize

    Returns:
        String representation like ``"10.00"``
    """
    return f'{quantize_cents(amount):.2f}'
