"""Transfers: idempotency, insufficient funds, concurrency."""

import asyncio

from uuid import uuid4

from tests.helpers import WalletApi


async def test_transfer_moves_money(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')

    response = await api.transfer(alice, bob.id, '5.00')

    assert response.status_code == 201
    body = response.json()
    assert body['amount'] == '5.00'
    assert body['balance_usd'] == '5.00'
    assert (await api.balance(alice))['balance_usd'] == '5.00'
    assert (await api.balance(bob))['balance_usd'] == '5.00'


async def test_same_key_same_body_returns_same_response_without_second_debit(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')

    first = await api.transfer(alice, bob.id, '5.00', idempotency_key='key-1')
    second = await api.transfer(alice, bob.id, '5.00', idempotency_key='key-1')

    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert second.headers['Idempotent-Replayed'] == 'true'
    assert (await api.balance(alice))['balance_usd'] == '5.00'
    assert (await api.balance(bob))['balance_usd'] == '5.00'


async def test_same_key_different_body_returns_409(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')

    await api.transfer(alice, bob.id, '5.00', idempotency_key='key-1')
    conflict = await api.transfer(alice, bob.id, '6.00', idempotency_key='key-1')

    assert conflict.status_code == 409
    assert conflict.json()['error']['code'] == 'idempotency_key_conflict'
    assert (await api.balance(alice))['balance_usd'] == '5.00'


async def test_idempotency_keys_are_scoped_per_account(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob', balance='10.00')

    first = await api.transfer(alice, bob.id, '1.00', idempotency_key='shared')
    second = await api.transfer(bob, alice.id, '2.00', idempotency_key='shared')

    assert first.status_code == second.status_code == 201
    assert first.json()['transfer_id'] != second.json()['transfer_id']


async def test_insufficient_funds(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='3.00')
    bob = await api.create_account('bob')

    response = await api.transfer(alice, bob.id, '5.00')

    assert response.status_code == 409
    error = response.json()['error']
    assert error['code'] == 'insufficient_funds'
    assert error['details'] == {'balance_usd': '3.00', 'required_usd': '5.00'}
    assert (await api.balance(alice))['balance_usd'] == '3.00'


async def test_failed_attempt_is_not_cached_for_the_key(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='3.00')
    bob = await api.create_account('bob')

    failed = await api.transfer(alice, bob.id, '5.00', idempotency_key='retry-me')
    await api.set_balance(alice, '10.00')
    retried = await api.transfer(alice, bob.id, '5.00', idempotency_key='retry-me')

    assert failed.status_code == 409
    assert retried.status_code == 201
    assert (await api.balance(alice))['balance_usd'] == '5.00'


async def test_missing_idempotency_key_returns_400(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')

    response = await api.client.post(
        '/v1/transfers',
        json={'to_account_id': bob.id, 'amount': '1.00'},
        headers=alice.headers,
    )

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'idempotency_key_required'


async def test_transfer_to_self_returns_400(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')

    response = await api.transfer(alice, alice.id, '1.00')

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'invalid_transfer'


async def test_transfer_to_unknown_account_returns_404(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')

    response = await api.transfer(alice, str(uuid4()), '1.00')

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'account_not_found'
    assert (await api.balance(alice))['balance_usd'] == '10.00'


async def test_invalid_amounts_return_422(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')
    headers = {**alice.headers, 'Idempotency-Key': 'k'}

    for amount in [1.5, '0.001', '0.00', '-1.00', 'abc']:
        response = await api.client.post(
            '/v1/transfers',
            json={'to_account_id': bob.id, 'amount': amount},
            headers=headers,
        )
        assert response.status_code == 422, amount
        assert response.json()['error']['code'] == 'validation_error'


async def test_minimum_amount_is_one_cent(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='0.01')
    bob = await api.create_account('bob')

    response = await api.transfer(alice, bob.id, '0.01')

    assert response.status_code == 201
    assert (await api.balance(alice))['balance_usd'] == '0.00'


async def test_concurrent_transfers_never_overdraw(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')

    responses = await asyncio.gather(*[api.transfer(alice, bob.id, '1.00') for _ in range(25)])

    statuses = sorted(r.status_code for r in responses)
    assert statuses.count(201) == 10
    assert statuses.count(409) == 15
    assert (await api.balance(alice))['balance_usd'] == '0.00'
    assert (await api.balance(bob))['balance_usd'] == '10.00'


async def test_concurrent_requests_with_same_key_debit_once(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')

    responses = await asyncio.gather(
        *[api.transfer(alice, bob.id, '1.00', idempotency_key='same') for _ in range(10)],
    )

    assert {r.status_code for r in responses} == {201}
    assert len({r.json()['transfer_id'] for r in responses}) == 1
    assert (await api.balance(alice))['balance_usd'] == '9.00'


async def test_opposite_concurrent_transfers_do_not_deadlock(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='50.00')
    bob = await api.create_account('bob', balance='50.00')

    responses = await asyncio.gather(
        *[api.transfer(alice, bob.id, '1.00') for _ in range(10)],
        *[api.transfer(bob, alice.id, '1.00') for _ in range(10)],
    )

    assert {r.status_code for r in responses} == {201}
    assert (await api.balance(alice))['balance_usd'] == '50.00'
    assert (await api.balance(bob))['balance_usd'] == '50.00'
