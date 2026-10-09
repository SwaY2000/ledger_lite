"""Webhook signature verifier implementations.

The provider signs every webhook as::

    X-Timestamp: <unix seconds>
    X-Signature: sha256=<hex HMAC-SHA256(secret, f"{timestamp}.{raw_body}")>

The timestamp is part of the signed message, so a captured request cannot be
replayed after the tolerance window even though its signature stays valid.
"""

import hashlib
import hmac
import time

from collections.abc import Callable
from typing import Protocol

from src.errors import InvalidSignatureError


__all__ = (
    'IWebhookSignatureVerifier',
    'HmacWebhookSignatureVerifier',
)


class IWebhookSignatureVerifier(Protocol):
    """Protocol for webhook signature verification."""

    def __call__(self, raw_body: bytes, signature: str | None, timestamp: str | None) -> None:
        """Verify a webhook signature.

        Args:
            raw_body: Exact request body bytes
            signature: Value of the X-Signature header
            timestamp: Value of the X-Timestamp header

        Raises:
            InvalidSignatureError: If the signature is missing, invalid or expired
        """


class HmacWebhookSignatureVerifier:
    """HMAC-SHA256 webhook signature verifier with timestamp tolerance."""

    def __init__(self, secret: str, tolerance_seconds: int = 300, clock: Callable[[], float] = time.time) -> None:
        """Initialize the verifier.

        Args:
            secret: Shared webhook secret
            tolerance_seconds: Allowed clock difference in both directions
            clock: Source of the current unix time (injectable for tests)
        """
        self._secret = secret.encode()
        self._tolerance_seconds = tolerance_seconds
        self._clock = clock

    def __call__(self, raw_body: bytes, signature: str | None, timestamp: str | None) -> None:
        """Verify the signature and freshness of a webhook."""
        if not signature or not timestamp:
            raise InvalidSignatureError('Missing X-Signature or X-Timestamp header')

        try:
            timestamp_value = int(timestamp)
        except ValueError as e:
            raise InvalidSignatureError('X-Timestamp must be a unix timestamp') from e

        if abs(self._clock() - timestamp_value) > self._tolerance_seconds:
            raise InvalidSignatureError('Webhook timestamp is outside the allowed tolerance')

        expected = 'sha256=' + hmac.new(self._secret, timestamp.encode() + b'.' + raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise InvalidSignatureError
