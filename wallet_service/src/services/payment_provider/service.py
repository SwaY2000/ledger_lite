"""Payment provider client implementations.

The wallet service talks to the provider synchronously with strict
timeouts. Network failures, timeouts and 5xx responses are translated into
``ProviderUnavailableError`` (HTTP 502), so clients get a clear, retryable
error instead of hanging requests or generic 500s.
"""

import logging

from decimal import Decimal
from typing import Any, Protocol

import httpx

from src.entities.money import format_money, parse_money
from src.errors import ProviderError, ProviderUnavailableError
from src.infrastructure.api_client import IAsyncClient

from .dtos import ProviderInvoice
from .enums import ProviderInvoiceStatuses


__all__ = (
    'IPaymentProviderService',
    'HttpPaymentProviderService',
)

logger = logging.getLogger(__name__)


class IPaymentProviderService(Protocol):
    """Protocol for the payment provider client."""

    async def create_invoice(self, amount: Decimal, external_id: str, callback_url: str) -> ProviderInvoice:
        """Create an invoice for a deposit.

        Args:
            amount: Amount to pay
            external_id: Deposit identifier on our side
            callback_url: URL the provider sends webhooks to

        Returns:
            Created invoice with ``pay_url``

        Raises:
            ProviderUnavailableError: Provider timed out, unreachable or 5xx
            ProviderError: Provider rejected the request or returned malformed data
        """

    async def get_invoice(self, invoice_id: str) -> ProviderInvoice | None:
        """Fetch the current invoice state.

        Args:
            invoice_id: Provider invoice identifier

        Returns:
            Invoice state, or None if the provider does not know the invoice

        Raises:
            ProviderUnavailableError: Provider timed out, unreachable or 5xx
            ProviderError: Provider rejected the request or returned malformed data
        """


class HttpPaymentProviderService:
    """Payment provider client over HTTP with bearer authentication."""

    def __init__(self, api_client: IAsyncClient, base_url: str, api_key: str) -> None:
        """Initialize the provider client.

        Args:
            api_client: Async HTTP client configured with request timeouts
            base_url: Provider base URL
            api_key: Provider API key sent as a bearer token
        """
        self._api_client = api_client
        self._base_url = base_url.rstrip('/')
        self._api_key = api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self._api_key}'}

    async def create_invoice(self, amount: Decimal, external_id: str, callback_url: str) -> ProviderInvoice:
        """Create an invoice for a deposit at the provider."""
        status_code, data = await self._call(
            'post',
            '/invoices',
            data={
                'amount': format_money(amount),
                'currency': 'USD',
                'external_id': external_id,
                'callback_url': callback_url,
            },
        )
        if status_code != 201:
            raise ProviderError(details={'provider_status': status_code, 'provider_response': data})

        invoice = self._parse_invoice(data)
        if not invoice.pay_url:
            raise ProviderError('Provider response does not contain pay_url')
        return invoice

    async def get_invoice(self, invoice_id: str) -> ProviderInvoice | None:
        """Fetch the current invoice state from the provider."""
        status_code, data = await self._call('get', f'/invoices/{invoice_id}')
        if status_code == 404:
            return None
        if status_code != 200:
            raise ProviderError(details={'provider_status': status_code, 'provider_response': data})
        return self._parse_invoice(data)

    async def _call(self, method: str, path: str, **kwargs: Any) -> tuple[int, Any]:
        """Perform a provider request translating transport failures into domain errors."""
        try:
            status_code, data = await getattr(self._api_client, method)(
                url=f'{self._base_url}{path}',
                headers=self._headers,
                **kwargs,
            )
        except httpx.TimeoutException as e:
            raise ProviderUnavailableError(details={'reason': 'timeout'}) from e
        except httpx.HTTPError as e:
            raise ProviderUnavailableError(details={'reason': type(e).__name__}) from e

        if status_code >= 500:
            logger.warning(f'Provider returned {status_code} for {method.upper()} {path}')
            raise ProviderUnavailableError(details={'provider_status': status_code})
        return status_code, data

    @staticmethod
    def _parse_invoice(data: Any) -> ProviderInvoice:
        """Parse an invoice payload returned by the provider."""
        try:
            paid_amount = data.get('paid_amount')
            return ProviderInvoice(
                invoice_id=str(data['invoice_id']),
                status=ProviderInvoiceStatuses(data['status']),
                paid_amount=parse_money(paid_amount, allow_zero=True) if paid_amount is not None else None,
                pay_url=data.get('pay_url'),
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            raise ProviderError('Malformed provider response', details={'provider_response': data}) from e
