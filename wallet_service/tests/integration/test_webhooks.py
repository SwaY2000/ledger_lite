"""Provider webhook: signature, deduplication, settlement rules."""

import asyncio
import time

from tests.fakes import FakePaymentProvider
from tests.helpers import WalletApi


async def test_paid_webhook_credits_amount_minus_fee(api: WalletApi, fake_provider: FakePaymentProvider) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account, '10.00')

    response = await api.webhook(deposit['invoice_id'], 'paid', '10.00')

    assert response.status_code == 200
    assert response.json() == {'result': 'processed', 'deposit_id': deposit['deposit_id']}
    assert (await api.balance(account))['balance_usd'] == '9.85'


async def test_partially_paid_credits_actually_paid_amount(api: WalletApi, fake_provider: FakePaymentProvider) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account, '10.00')

    await api.webhook(deposit['invoice_id'], 'partially_paid', '7.50')

    # 7.50 * 1.5% = 0.1125 -> 0.11 fee
    assert (await api.balance(account))['balance_usd'] == '7.39'


async def test_duplicate_event_id_is_credited_once(api: WalletApi, fake_provider: FakePaymentProvider) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account, '10.00')

    first = await api.webhook(deposit['invoice_id'], 'paid', '10.00', event_id='evt_1')
    second = await api.webhook(deposit['invoice_id'], 'paid', '10.00', event_id='evt_1')

    assert first.json()['result'] == 'processed'
    assert second.status_code == 200
    assert second.json()['result'] == 'duplicate'
    assert (await api.balance(account))['balance_usd'] == '9.85'


async def test_concurrent_duplicate_deliveries_are_credited_once(
    api: WalletApi,
    fake_provider: FakePaymentProvider,
) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account, '10.00')

    responses = await asyncio.gather(
        *[api.webhook(deposit['invoice_id'], 'paid', '10.00', event_id='evt_same') for _ in range(5)],
    )

    assert sorted(r.json()['result'] for r in responses) == ['duplicate'] * 4 + ['processed']
    assert (await api.balance(account))['balance_usd'] == '9.85'


async def test_different_events_for_closed_deposit_change_nothing(
    api: WalletApi,
    fake_provider: FakePaymentProvider,
) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account, '10.00')

    await api.webhook(deposit['invoice_id'], 'paid', '10.00')
    late = await api.webhook(deposit['invoice_id'], 'paid', '10.00')

    assert late.status_code == 200
    assert late.json()['result'] == 'ignored'
    assert (await api.balance(account))['balance_usd'] == '9.85'


async def test_expired_closes_deposit_and_late_payment_is_ignored(
    api: WalletApi,
    fake_provider: FakePaymentProvider,
) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account, '10.00')

    expired = await api.webhook(deposit['invoice_id'], 'expired')
    late_paid = await api.webhook(deposit['invoice_id'], 'paid', '10.00')

    assert expired.json()['result'] == 'processed'
    assert late_paid.json()['result'] == 'ignored'
    assert (await api.balance(account))['balance_usd'] == '0.00'


async def test_valid_signature_is_accepted(api: WalletApi, fake_provider: FakePaymentProvider) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account)

    response = await api.webhook(deposit['invoice_id'], 'paid', '10.00', timestamp=int(time.time()) - 299)

    assert response.status_code == 200


async def test_wrong_signature_is_rejected(api: WalletApi, fake_provider: FakePaymentProvider) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account)

    response = await api.webhook(deposit['invoice_id'], 'paid', '10.00', secret='wrong-secret')

    assert response.status_code == 401
    assert response.json()['error']['code'] == 'invalid_signature'
    assert (await api.balance(account))['balance_usd'] == '0.00'


async def test_expired_timestamp_is_rejected(api: WalletApi, fake_provider: FakePaymentProvider) -> None:
    account = await api.create_account()
    deposit = await api.deposit(account)

    response = await api.webhook(deposit['invoice_id'], 'paid', '10.00', timestamp=int(time.time()) - 301)

    assert response.status_code == 401
    assert response.json()['error']['code'] == 'invalid_signature'
    assert (await api.balance(account))['balance_usd'] == '0.00'


async def test_missing_signature_headers_are_rejected(api: WalletApi) -> None:
    response = await api.client.post('/v1/webhooks/provider', content=b'{}')

    assert response.status_code == 401
    assert response.json()['error']['code'] == 'invalid_signature'


async def test_unknown_invoice_returns_404_and_can_be_redelivered(
    api: WalletApi,
    fake_provider: FakePaymentProvider,
) -> None:
    response = await api.webhook('inv_unknown', 'paid', '10.00', event_id='evt_unknown')
    retry = await api.webhook('inv_unknown', 'paid', '10.00', event_id='evt_unknown')

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'deposit_not_found'
    assert retry.status_code == 404  # event was not stored, so a later redelivery is not lost


async def test_malformed_payload_returns_422(api: WalletApi) -> None:
    response = await api.webhook('inv_1', 'paid', '10.001')

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'
