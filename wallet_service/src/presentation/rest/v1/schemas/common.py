"""Common API schemas used across multiple endpoints.

This module defines reusable Pydantic types for monetary amounts and the
unified error response schema shared by all endpoints.
"""

from decimal import Decimal
from typing import Annotated, Any

from fastapi import status
from pydantic import BaseModel, Field, PlainSerializer, PlainValidator, WithJsonSchema

from src.entities.money import format_money, parse_money


__all__ = (
    'MoneyAmount',
    'MoneyOut',
    'ErrorDetailSchema',
    'ErrorSchema',
    'error_doc',
)


MoneyAmount = Annotated[
    Decimal,
    PlainValidator(parse_money),
    PlainSerializer(format_money, return_type=str),
    WithJsonSchema({'type': 'string', 'pattern': r'^\d{1,10}(\.\d{1,2})?$', 'examples': ['10.00']}),
]
"""Positive amount received as a JSON string with at most two decimals.

Numbers (``10.0``) and strings with more than two decimals (``"1.001"``)
are rejected with 422 to avoid float rounding issues.
"""

MoneyOut = Annotated[
    Decimal,
    PlainSerializer(format_money, return_type=str),
    WithJsonSchema({'type': 'string', 'examples': ['9.85']}),
]
"""Amount serialized as a JSON string with exactly two decimals."""


class ErrorDetailSchema(BaseModel):
    """Error description inside the unified error envelope.

    Attributes:
        code: Stable machine-readable error code
        message: Human-readable error description
        details: Additional structured information
    """

    code: str = Field(description='Stable machine-readable error code', examples=['insufficient_funds'])
    message: str = Field(description='Human-readable error message', examples=['Insufficient funds'])
    details: dict[str, Any] = Field(default_factory=dict, description='Additional structured information')


class ErrorSchema(BaseModel):
    """Standard API error response schema used by every endpoint."""

    error: ErrorDetailSchema


_DEFAULT_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: 'Malformed request',
    status.HTTP_401_UNAUTHORIZED: 'Missing or invalid credentials',
    status.HTTP_404_NOT_FOUND: 'Resource not found',
    status.HTTP_409_CONFLICT: 'Conflict with the current state',
    status.HTTP_422_UNPROCESSABLE_CONTENT: 'Request validation failed',
    status.HTTP_429_TOO_MANY_REQUESTS: 'Rate limit exceeded, see Retry-After header',
    status.HTTP_502_BAD_GATEWAY: 'Payment provider is unavailable or rejected the request',
}


def error_doc(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Build OpenAPI response docs for error status codes.

    Args:
        *status_codes: HTTP status codes the endpoint may return

    Returns:
        Mapping suitable for the ``responses`` argument of a route
    """
    return {code: {'model': ErrorSchema, 'description': _DEFAULT_MESSAGES.get(code, 'Error')} for code in status_codes}
