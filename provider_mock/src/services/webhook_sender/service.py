"""Webhook sender service.

Signs the exact body bytes as ``HMAC-SHA256(secret, f"{timestamp}.{raw_body}")``
and sends them with ``X-Signature: sha256=<hex>`` and ``X-Timestamp: <unix>``.
"""

import datetime
import hashlib
import hmac
import logging
import time

from dataclasses import dataclass
from typing import Protocol

import httpx

from pydantic import BaseModel

from src.infrastructure.api_client import IAsyncClient


__all__ = (
    'WebhookEvent',
    'DeliveryResult',
    'IWebhookSenderService',
    'WebhookSenderService',
)

logger = logging.getLogger(__name__)


class WebhookEvent(BaseModel):
    """Webhook payload."""

    event_id: str
    invoice_id: str
    status: str
    paid_amount: str
    occurred_at: datetime.datetime


@dataclass
class DeliveryResult:
    """Outcome of a single delivery attempt.

    Attributes:
        status_code: HTTP status returned by the receiver (None on transport error)
        error: Transport error description
    """

    status_code: int | None = None
    error: str | None = None


class IWebhookSenderService(Protocol):
    """Protocol for webhook delivery."""

    async def __call__(self, url: str, event: WebhookEvent, times: int = 1) -> list[DeliveryResult]:
        """Deliver the same event ``times`` times."""


class WebhookSenderService:
    """Delivers signed webhooks over HTTP."""

    def __init__(self, api_client: IAsyncClient, secret: str) -> None:
        """Initialize the sender.

        Args:
            api_client: Async HTTP client with timeouts
            secret: Shared webhook secret
        """
        self._api_client = api_client
        self._secret = secret.encode()

    def sign(self, body: bytes, timestamp: str) -> str:
        """Compute the X-Signature header value."""
        return 'sha256=' + hmac.new(self._secret, timestamp.encode() + b'.' + body, hashlib.sha256).hexdigest()

    async def __call__(self, url: str, event: WebhookEvent, times: int = 1) -> list[DeliveryResult]:
        """Deliver the same event (same event_id) ``times`` times, sequentially."""
        body = event.model_dump_json().encode()
        results = []
        for _ in range(times):
            timestamp = str(int(time.time()))
            headers = {
                'Content-Type': 'application/json',
                'X-Timestamp': timestamp,
                'X-Signature': self.sign(body, timestamp),
            }
            try:
                status_code, _ = await self._api_client.post(url=url, headers=headers, content=body)
                results.append(DeliveryResult(status_code=status_code))
            except httpx.HTTPError as e:
                logger.warning(f'Webhook delivery to {url} failed: {e!r}')
                results.append(DeliveryResult(error=type(e).__name__))
        return results
