"""API documentation for transfer endpoints."""

from typing import Any

from fastapi import status

from src.presentation.rest.v1.schemas.common import error_doc


__all__ = ('CREATE_TRANSFER_DOCS',)


CREATE_TRANSFER_DOCS: dict[str, Any] = {
    'summary': 'Create Transfer',
    'description': """
    Transfers money to another account. No fee, minimum amount `"0.01"`.

    **Idempotency:** the `Idempotency-Key` header is required.
    - same key + same body: the original response is returned, money is moved only once
      (the response carries `Idempotent-Replayed: true`);
    - same key + different body: `409 idempotency_key_conflict`;
    - a failed attempt (e.g. `insufficient_funds`) is not stored and may be retried with the same key.

    **Consistency:** both balances are updated in one transaction under row locks; the balance never
    becomes negative, even with concurrent requests.
    """,
    'responses': error_doc(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
    ),
    'operation_id': 'create_transfer',
}
