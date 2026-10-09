"""API documentation for account endpoints."""

from typing import Any

from fastapi import status

from src.presentation.rest.v1.schemas.common import error_doc


__all__ = ('GET_ME_DOCS',)


GET_ME_DOCS: dict[str, Any] = {
    'summary': 'Get Current Account',
    'description': """
    Returns the balances of the account owning the API key.

    - `balance_usd` is a decimal string with exactly two fractional digits.
    - `credits` is the number of purchased credits.
    """,
    'responses': error_doc(status.HTTP_401_UNAUTHORIZED),
    'operation_id': 'get_current_account',
}
