"""API documentation for purchase endpoints."""

from typing import Any

from fastapi import status

from src.presentation.rest.v1.schemas.common import error_doc


__all__ = ('CREATE_PURCHASE_DOCS',)


CREATE_PURCHASE_DOCS: dict[str, Any] = {
    'summary': 'Buy Credits',
    'description': """
    Buys credits with the USD balance.

    **Pricing:** 0.10 USD per credit; 5% discount from 500 credits, 12.5% discount from 1000 credits.
    The final price is rounded to cents with ROUND_HALF_UP (e.g. 507 credits cost 48.17).
    """,
    'responses': error_doc(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
    ),
    'operation_id': 'create_purchase',
}
