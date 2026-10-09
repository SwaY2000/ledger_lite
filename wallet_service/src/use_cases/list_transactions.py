"""Use case for the paginated operation history."""

import base64
import binascii
import datetime

from uuid import UUID

from src.errors import InvalidCursorError
from src.repositories.interfaces import IUnitOfWork

from .dtos import ListTransactionsInput, ListTransactionsOutput


__all__ = (
    'ListTransactionsUseCase',
    'encode_cursor',
    'decode_cursor',
)


def encode_cursor(created_at: datetime.datetime, transaction_id: str) -> str:
    """Encode a keyset position into an opaque URL-safe cursor."""
    return base64.urlsafe_b64encode(f'{created_at.isoformat()}|{transaction_id}'.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime.datetime, str]:
    """Decode an opaque cursor into a keyset position.

    Raises:
        InvalidCursorError: If the cursor is malformed
    """
    try:
        created_at, transaction_id = base64.urlsafe_b64decode(cursor.encode()).decode().split('|', 1)
        return datetime.datetime.fromisoformat(created_at), str(UUID(transaction_id))
    except (binascii.Error, UnicodeDecodeError, ValueError) as e:
        raise InvalidCursorError from e


class ListTransactionsUseCase:
    """Use case returning account transactions with keyset (cursor) pagination.

    Keyset pagination keeps pages stable while new transactions are added,
    unlike offset pagination which would shift items between pages.
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow

    async def __call__(self, request: ListTransactionsInput) -> ListTransactionsOutput:
        """List account transactions, newest first.

        Args:
            request: Input DTO with account, page size and cursor

        Returns:
            Page of transactions and the cursor of the next page

        Raises:
            InvalidCursorError: If the cursor is malformed
        """
        before = decode_cursor(request.cursor) if request.cursor else None

        async with self._uow:
            items = await self._uow.transactions.list_by_account(request.account_id, request.limit + 1, before)

        next_cursor = None
        if len(items) > request.limit:
            items = items[: request.limit]
            next_cursor = encode_cursor(items[-1].created_at, items[-1].ID)

        return ListTransactionsOutput(items=items, next_cursor=next_cursor)
