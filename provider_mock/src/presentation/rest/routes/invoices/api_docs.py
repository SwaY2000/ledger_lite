"""API documentation for invoice endpoints."""

from typing import Any


__all__ = (
    'CREATE_INVOICE_DOCS',
    'GET_INVOICE_DOCS',
    'SIMULATE_INVOICE_DOCS',
)


CREATE_INVOICE_DOCS: dict[str, Any] = {
    'summary': 'Create Invoice',
    'description': 'Creates a pending invoice and returns its payment URL.',
    'operation_id': 'create_invoice',
}

GET_INVOICE_DOCS: dict[str, Any] = {
    'summary': 'Get Invoice',
    'description': 'Returns the current status (pending, paid, partially_paid, expired) and paid_amount.',
    'operation_id': 'get_invoice',
}

SIMULATE_INVOICE_DOCS: dict[str, Any] = {
    'summary': 'Simulate Payment Outcome',
    'description': """
    Moves a pending invoice to a final status. Final statuses never change again (409).

    With `deliver_webhook: true` a signed webhook is sent to `callback_url`
    (`duplicate: true` sends the same event twice). Delivery results are returned for convenience.
    """,
    'operation_id': 'simulate_invoice',
}
