"""Money rules: tables from the task statement plus boundaries."""

from decimal import Decimal

import pytest

from src.entities.account import AccountEntity
from src.entities.money import (
    calculate_credits_price,
    calculate_net_deposit,
    calculate_provider_fee,
    format_money,
    parse_money,
)
from src.errors import InsufficientFundsError


@pytest.mark.parametrize(
    ('paid', 'fee', 'credited'),
    [
        ('10.00', '0.15', '9.85'),
        ('0.99', '0.01', '0.98'),
        ('33.33', '0.50', '32.83'),
        ('0.01', '0.00', '0.01'),
        ('100.00', '1.50', '98.50'),
    ],
)
def test_provider_fee_table(paid: str, fee: str, credited: str) -> None:
    assert calculate_provider_fee(Decimal(paid)) == Decimal(fee)
    assert calculate_net_deposit(Decimal(paid)) == Decimal(credited)


@pytest.mark.parametrize(
    ('quantity', 'price'),
    [
        (333, '33.30'),
        (507, '48.17'),
        (1005, '87.94'),
        (1, '0.10'),
        (499, '49.90'),
        (500, '47.50'),
        (999, '94.91'),
        (1000, '87.50'),
    ],
)
def test_credits_price_table(quantity: int, price: str) -> None:
    assert calculate_credits_price(quantity) == Decimal(price)


@pytest.mark.parametrize('quantity', [0, -1])
def test_credits_price_rejects_non_positive(quantity: int) -> None:
    with pytest.raises(ValueError):
        calculate_credits_price(quantity)


@pytest.mark.parametrize(
    ('raw', 'expected'),
    [('10.00', '10.00'), ('10', '10.00'), ('0.5', '0.50'), ('0.01', '0.01')],
)
def test_parse_money_accepts_strings(raw: str, expected: str) -> None:
    assert parse_money(raw) == Decimal(expected)


@pytest.mark.parametrize('raw', [10.0, 10, None, '10.001', '-1.00', '1e3', 'abc', '', '0.00', ' 1.00'])
def test_parse_money_rejects_invalid(raw: object) -> None:
    with pytest.raises(ValueError):
        parse_money(raw)


def test_parse_money_allows_zero_when_requested() -> None:
    assert parse_money('0.00', allow_zero=True) == Decimal('0.00')


def test_format_money_always_two_decimals() -> None:
    assert format_money(Decimal('9.8')) == '9.80'
    assert format_money(Decimal('0')) == '0.00'


def test_account_debit_never_goes_negative() -> None:
    account = AccountEntity(name='alice', api_key_hash='x', balance_usd=Decimal('5.00'))

    with pytest.raises(InsufficientFundsError):
        account.debit(Decimal('5.01'))

    account.debit(Decimal('5.00'))
    assert account.balance_usd == Decimal('0.00')
