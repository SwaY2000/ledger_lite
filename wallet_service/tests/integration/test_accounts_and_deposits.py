"""Authentication, account balances and deposit creation."""

from typing import Any

from dependency_injector import providers
from sqlalchemy import text

from src.errors import ProviderUnavailableError
from src.infrastructure.api_client import AsyncHTTPXApiClient
from src.services.payment_provider import HttpPaymentProviderService
from tests.fakes import FakePaymentProvider
from tests.helpers import WalletApi


async def test_me_returns_balances(api: WalletApi) -> None:
    account = await api.create_account('alice', balance='12.34')

    body = await api.balance(account)

    assert body == {'account_id': account.id, 'name': 'alice', 'balance_usd': '12.34', 'credits': 0}


async def test_missing_api_key_returns_401_in_unified_format(api: WalletApi) -> None:
    response = await api.client.get('/v1/accounts/me')

    assert response.status_code == 401
    assert response.json() == {
        'error': {'code': 'unauthorized', 'message': 'Missing or invalid API key', 'details': {}},
    }


async def test_unknown_api_key_returns_401(api: WalletApi) -> None:
    response = await api.client.get('/v1/accounts/me', headers={'X-API-Key': 'll_unknown'})

    assert response.status_code == 401


async def test_api_key_is_not_stored_in_plain_text(api: WalletApi, container: Any) -> None:
    account = await api.create_account()

    async with container.postgres_database().engine.connect() as connection:
        stored = await connection.scalar(text('SELECT api_key_hash FROM accounts WHERE id = :id'), {'id': account.id})

    assert stored != account.api_key
    assert account.api_key not in stored


async def test_unknown_route_uses_unified_error_format(api: WalletApi) -> None:
    response = await api.client.get('/v1/unknown')

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'not_found'


async def test_create_deposit_returns_pay_url(api: WalletApi, fake_provider: FakePaymentProvider) -> None:
    account = await api.create_account()

    deposit = await api.deposit(account, '10.00')

    assert deposit['status'] == 'pending'
    assert deposit['amount'] == '10.00'
    assert deposit['pay_url'].startswith('http://provider.test/pay/')
    assert deposit['invoice_id'] in fake_provider.invoices


async def test_deposit_amount_must_be_a_string_with_two_decimals(api: WalletApi) -> None:
    account = await api.create_account()

    as_number = await api.client.post('/v1/deposits', json={'amount': 10.0}, headers=account.headers)
    three_decimals = await api.client.post('/v1/deposits', json={'amount': '10.001'}, headers=account.headers)

    assert as_number.status_code == 422
    assert three_decimals.status_code == 422
    assert as_number.json()['error']['details']['errors'][0]['loc'] == ['body', 'amount']


async def test_provider_failure_returns_502_and_marks_deposit_failed(
    api: WalletApi,
    fake_provider: FakePaymentProvider,
    container: Any,
) -> None:
    account = await api.create_account()
    fake_provider.error = ProviderUnavailableError(details={'reason': 'timeout'})

    response = await api.client.post('/v1/deposits', json={'amount': '10.00'}, headers=account.headers)

    assert response.status_code == 502
    error = response.json()['error']
    assert error['code'] == 'provider_unavailable'
    async with container.postgres_database().engine.connect() as connection:
        status = await connection.scalar(
            text('SELECT status FROM deposits WHERE id = :id'),
            {'id': error['details']['deposit_id']},
        )
    assert status == 'failed'


async def test_unreachable_provider_returns_502(api: WalletApi, container: Any) -> None:
    # The real HTTP client against a closed port: connection refused -> 502, no hanging request.
    container.payment_provider_service.override(
        providers.Object(
            HttpPaymentProviderService(
                api_client=AsyncHTTPXApiClient(timeout=1),
                base_url='http://127.0.0.1:9',
                api_key='key',
            ),
        ),
    )
    account = await api.create_account()

    response = await api.client.post('/v1/deposits', json={'amount': '10.00'}, headers=account.headers)

    assert response.status_code == 502
    assert response.json()['error']['code'] == 'provider_unavailable'
