"""Idempotency record entity module.

Stores the response of a processed request keyed by (account, Idempotency-Key),
so that retries return exactly the same response without repeating side effects.
"""

from typing import Any

from pydantic import Field

from src.entities.base import BaseEntity


__all__ = ('IdempotencyRecordEntity',)


class IdempotencyRecordEntity(BaseEntity):
    """Entity representing a stored idempotent request.

    Attributes:
        account_id: Account that issued the request
        key: Client-provided Idempotency-Key header value
        request_hash: SHA-256 of the canonical request body
        response_status: HTTP status of the stored response
        response_body: JSON body of the stored response
    """

    account_id: str = Field(..., description='Account that issued the request')
    key: str = Field(..., description='Idempotency-Key header value')
    request_hash: str = Field(..., description='SHA-256 of the canonical request body')
    response_status: int | None = Field(default=None, description='HTTP status of the stored response')
    response_body: dict[str, Any] | None = Field(default=None, description='JSON body of the stored response')

    def store_response(self, status: int, body: dict[str, Any]) -> None:
        """Remember the response to replay it on retries.

        Args:
            status: HTTP status code
            body: JSON-serializable response body
        """
        self.response_status = status
        self.response_body = body
        self.touch()
