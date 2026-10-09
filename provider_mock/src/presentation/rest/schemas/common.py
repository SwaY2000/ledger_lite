"""Common API schemas."""

from decimal import Decimal
from functools import partial
from typing import Annotated

from pydantic import PlainSerializer, PlainValidator, WithJsonSchema

from src.entities.money import format_money, parse_money


__all__ = (
    'MoneyAmount',
    'PaidAmount',
    'MoneyOut',
)


MoneyAmount = Annotated[
    Decimal,
    PlainValidator(parse_money),
    WithJsonSchema({'type': 'string', 'examples': ['10.00']}),
]
"""Positive amount as a decimal string."""

PaidAmount = Annotated[
    Decimal,
    PlainValidator(partial(parse_money, allow_zero=True)),
    WithJsonSchema({'type': 'string', 'examples': ['7.50']}),
]
"""Non-negative amount as a decimal string."""

MoneyOut = Annotated[Decimal, PlainSerializer(format_money, return_type=str), WithJsonSchema({'type': 'string'})]
"""Amount serialized as a string with two decimals."""
