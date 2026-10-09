"""Provider client: timeouts and provider failures become clear domain errors."""

from decimal import Decimal
from typing import Any

import httpx
import pytest

from src.errors import ProviderError, ProviderUnavailableError
from src.services.payment_provider import HttpPaymentProviderService, ProviderInvoiceStatuses


class StubClient:
    """IAsyncClient stub returning a canned response or raising an error."""

    def __init__(self, response: tuple[int, Any] | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def _call(self, **kwargs: Any) -> tuple[int, Any]:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response

    async def post(self, url: str, **kwargs: Any) -> tuple[int, Any]:
        return await self._call(url=url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> tuple[int, Any]:
        return await self._call(url=url, **kwargs)


def _service(client: StubClient) -> HttpPaymentProviderService:
    return HttpPaymentProviderService(api_client=client, base_url='http://provider/', api_key='key')  # type: ignore[arg-type]


async def test_create_invoice_sends_authenticated_request() -> None:
    client = StubClient(response=(201, {'invoice_id': 'inv_1', 'status': 'pending', 'pay_url': 'http://pay'}))

    invoice = await _service(client).create_invoice(Decimal('10'), 'dep_1', 'http://callback')

    assert invoice.invoice_id == 'inv_1'
    assert invoice.status is ProviderInvoiceStatuses.PENDING
    call = client.calls[0]
    assert call['url'] == 'http://provider/invoices'
    assert call['headers'] == {'Authorization': 'Bearer key'}
    assert call['data'] == {
        'amount': '10.00',
        'currency': 'USD',
        'external_id': 'dep_1',
        'callback_url': 'http://callback',
    }


@pytest.mark.parametrize(
    'error',
    [httpx.ReadTimeout('timeout'), httpx.ConnectTimeout('timeout'), httpx.ConnectError('refused')],
)
async def test_transport_errors_become_provider_unavailable(error: Exception) -> None:
    with pytest.raises(ProviderUnavailableError):
        await _service(StubClient(error=error)).create_invoice(Decimal('10'), 'dep_1', 'http://callback')


async def test_provider_5xx_becomes_provider_unavailable() -> None:
    with pytest.raises(ProviderUnavailableError):
        await _service(StubClient(response=(503, {}))).create_invoice(Decimal('10'), 'dep_1', 'http://callback')


async def test_provider_4xx_becomes_provider_error() -> None:
    with pytest.raises(ProviderError):
        await _service(StubClient(response=(401, {'error': 'unauthorized'}))).create_invoice(
            Decimal('10'),
            'dep_1',
            'http://callback',
        )


async def test_malformed_response_becomes_provider_error() -> None:
    with pytest.raises(ProviderError):
        await _service(StubClient(response=(201, {'unexpected': True}))).create_invoice(
            Decimal('10'),
            'dep_1',
            'http://callback',
        )


async def test_get_invoice_parses_paid_amount_and_handles_404() -> None:
    paid = await _service(
        StubClient(response=(200, {'invoice_id': 'inv_1', 'status': 'partially_paid', 'paid_amount': '7.50'})),
    ).get_invoice('inv_1')
    missing = await _service(StubClient(response=(404, {}))).get_invoice('inv_x')

    assert paid is not None
    assert paid.status is ProviderInvoiceStatuses.PARTIALLY_PAID
    assert paid.paid_amount == Decimal('7.50')
    assert missing is None
