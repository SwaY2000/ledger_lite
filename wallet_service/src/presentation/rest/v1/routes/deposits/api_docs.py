"""API documentation for deposit endpoints."""

from typing import Any

from fastapi import status

from src.presentation.rest.v1.schemas.common import error_doc


__all__ = ('CREATE_DEPOSIT_DOCS',)


CREATE_DEPOSIT_DOCS: dict[str, Any] = {
    'summary': 'Create Deposit',
    'description': """
    Creates an invoice at the payment provider and returns its `pay_url`.

    **Process Flow:**
    1. Deposit is stored with status `pending`
    2. Invoice is created at the provider (with a strict timeout)
    3. The provider notifies the wallet with a signed webhook once the invoice is paid or expired
    4. The paid amount minus the 1.5% provider fee is credited to the balance

    **Provider failures:** on timeout, network error or provider 5xx the deposit is marked
    `failed` and `502 provider_unavailable` is returned; the request can be safely retried.
    """,
    'responses': error_doc(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_502_BAD_GATEWAY,
    ),
    'operation_id': 'create_deposit',
}
