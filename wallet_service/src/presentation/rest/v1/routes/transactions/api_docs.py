"""API documentation for transaction history endpoints."""

from typing import Any

from fastapi import status

from src.presentation.rest.v1.schemas.common import error_doc


__all__ = ('LIST_TRANSACTIONS_DOCS',)


LIST_TRANSACTIONS_DOCS: dict[str, Any] = {
    'summary': 'List Transactions',
    'description': """
    Returns the operation history of the account, newest first.

    **Pagination:** cursor-based. Pass `next_cursor` from the previous page as `?cursor=`.
    Pages stay stable while new operations are added.
    """,
    'responses': error_doc(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    'operation_id': 'list_transactions',
}
