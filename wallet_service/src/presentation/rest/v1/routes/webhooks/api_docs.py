"""API documentation for provider webhook endpoints."""

from typing import Any

from fastapi import status

from src.presentation.rest.v1.schemas.common import error_doc


__all__ = ('PROVIDER_WEBHOOK_DOCS',)


PROVIDER_WEBHOOK_DOCS: dict[str, Any] = {
    'summary': 'Payment Provider Webhook',
    'description': """
    Receives invoice status changes from the payment provider.

    **Authentication:** `X-Timestamp: <unix>` and `X-Signature: sha256=<hex>` where the signature is
    `HMAC-SHA256(secret, f"{timestamp}.{raw_body}")`. Requests with a missing or wrong signature or a
    timestamp more than 5 minutes away from the server time are rejected with 401.

    **Body:** `{"event_id", "invoice_id", "status", "paid_amount", "occurred_at"}`.

    **Guarantees:**
    - an event with an already processed `event_id` never credits money again;
    - `paid` / `partially_paid` credit `paid_amount - 1.5% fee`, `expired` closes without crediting;
    - an event for an already closed deposit changes nothing.

    Not subject to the client rate limit.
    """,
    'responses': error_doc(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ),
    'operation_id': 'provider_webhook',
}
