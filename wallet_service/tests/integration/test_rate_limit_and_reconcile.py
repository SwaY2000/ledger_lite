"""Bonus features: rate limiting and pending deposits reconciliation."""

from typing import Any

from dependency_injector import providers
from sqlalchemy import text

from src.infrastructure.rate_limiter import InMemoryRateLimiter
from src.services.payment_provider import ProviderInvoiceStatuses
from src.use_cases.dtos import ReconcileDepositsInput
from tests.fakes import FakePaymentProvider
from tests.helpers import WalletApi


async def test_post_requests_are_rate_limited_per_api_key(api: WalletApi, container: Any) -> None:
    container.rate_limiter.override(providers.Object(InMemoryRateLimiter(limit=3)))
    alice = await api.create_account('alice')
    bob = await api.create_account('bob')

    alice_responses = [
        await api.client.post('/v1/purchases', json={'credits': 1}, headers=alice.headers) for _ in range(4)
    ]
    bob_response = await api.client.post('/v1/purchases', json={'credits': 1}, headers=bob.headers)
    alice_get = await api.client.get('/v1/accounts/me', headers=alice.headers)

    assert [r.status_code for r in alice_responses[:3]] == [409, 409, 409]  # passed the limiter
    limited = alice_responses[3]
    assert limited.status_code == 429
    assert limited.json()['error']['code'] == 'rate_limit_exceeded'
    assert 1 <= int(limited.headers['Retry-After']) <= 60
    assert bob_response.status_code == 409  # other keys are not affected
    assert alice_get.status_code == 200  # GET requests are not limited


async def test_webhook_is_not_rate_limited(
    api: WalletApi,
    container: Any,
    fake_provider: FakePaymentProvider,
) -> None:
    container.rate_limiter.override(providers.Object(InMemoryRateLimiter(limit=1)))
    account = await api.create_account()
    deposit = await api.deposit(account)

    responses = [await api.webhook(deposit['invoice_id'], 'pending') for _ in range(5)]

    assert {r.status_code for r in responses} == {200}


async def _age_deposits(container: Any, minutes: int) -> None:
    async with container.postgres_database().engine.begin() as connection:
        await connection.execute(
            text(f"UPDATE deposits SET created_at = created_at - interval '{minutes} minutes'"),
        )


async def test_reconcile_settles_deposits_with_lost_webhooks(
    api: WalletApi,
    container: Any,
    fake_provider: FakePaymentProvider,
) -> None:
    account = await api.create_account()
    paid = await api.deposit(account, '10.00')
    expired = await api.deposit(account, '5.00')
    pending = await api.deposit(account, '1.00')
    fresh = await api.deposit(account, '2.00')
    await _age_deposits(container, 30)
    fresh_paid_later = await api.deposit(account, '3.00')
    fake_provider.set_status(paid['invoice_id'], ProviderInvoiceStatuses.PAID, '10.00')
    fake_provider.set_status(expired['invoice_id'], ProviderInvoiceStatuses.EXPIRED, '0.00')
    fake_provider.set_status(fresh_paid_later['invoice_id'], ProviderInvoiceStatuses.PAID, '3.00')

    reconcile = container.reconcile_deposits_use_case()
    result = await reconcile(ReconcileDepositsInput(older_than_minutes=15))
    second_run = await reconcile(ReconcileDepositsInput(older_than_minutes=15))

    assert (result.checked, result.settled, result.still_pending, result.errors) == (4, 2, 2, {})
    assert (second_run.checked, second_run.settled, second_run.still_pending) == (2, 0, 2)
    assert (await api.balance(account))['balance_usd'] == '9.85'  # fresh deposit is not touched yet
    assert pending['deposit_id'] and fresh['deposit_id']

    late_webhook = await api.webhook(paid['invoice_id'], 'paid', '10.00')
    assert late_webhook.json()['result'] == 'ignored'
    assert (await api.balance(account))['balance_usd'] == '9.85'
