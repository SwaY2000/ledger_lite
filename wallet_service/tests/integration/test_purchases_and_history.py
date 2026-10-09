"""Credit purchases and paginated history."""

from tests.helpers import WalletApi


async def test_purchase_charges_tier_price(api: WalletApi) -> None:
    account = await api.create_account(balance='100.00')

    response = await api.client.post('/v1/purchases', json={'credits': 507}, headers=account.headers)

    assert response.status_code == 201
    body = response.json()
    assert body['price_usd'] == '48.17'
    assert body['balance_usd'] == '51.83'
    assert body['credits_balance'] == 507
    assert await api.balance(account) == {
        'account_id': account.id,
        'name': 'user',
        'balance_usd': '51.83',
        'credits': 507,
    }


async def test_purchase_with_insufficient_funds(api: WalletApi) -> None:
    account = await api.create_account(balance='33.29')

    response = await api.client.post('/v1/purchases', json={'credits': 333}, headers=account.headers)

    assert response.status_code == 409
    assert response.json()['error']['code'] == 'insufficient_funds'
    assert (await api.balance(account))['credits'] == 0


async def test_purchase_validates_credits(api: WalletApi) -> None:
    account = await api.create_account(balance='100.00')

    for value in ['10', 0, -5, 1.5]:
        response = await api.client.post('/v1/purchases', json={'credits': value}, headers=account.headers)
        assert response.status_code == 422, value


async def test_history_is_paginated_newest_first(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')
    for amount in ['1.00', '2.00', '3.00']:
        assert (await api.transfer(alice, bob.id, amount)).status_code == 201
    assert (await api.client.post('/v1/purchases', json={'credits': 10}, headers=alice.headers)).status_code == 201

    pages = []
    cursor = None
    while True:
        params = {'limit': 3} | ({'cursor': cursor} if cursor else {})
        response = await api.client.get('/v1/transactions', params=params, headers=alice.headers)
        assert response.status_code == 200
        body = response.json()
        pages.append(body['items'])
        cursor = body['next_cursor']
        if cursor is None:
            break

    items = [item for page in pages for item in page]
    assert [len(page) for page in pages] == [3, 1]
    assert [(i['type'], i['amount_usd'], i['credits']) for i in items] == [
        ('purchase', '-1.00', 10),
        ('transfer_out', '-3.00', 0),
        ('transfer_out', '-2.00', 0),
        ('transfer_out', '-1.00', 0),
    ]
    assert all(i['counterparty_account_id'] == bob.id for i in items[1:])


async def test_history_only_contains_own_transactions(api: WalletApi) -> None:
    alice = await api.create_account('alice', balance='10.00')
    bob = await api.create_account('bob')
    await api.transfer(alice, bob.id, '1.00')

    response = await api.client.get('/v1/transactions', headers=bob.headers)

    assert [(i['type'], i['amount_usd']) for i in response.json()['items']] == [('transfer_in', '1.00')]


async def test_invalid_cursor_returns_400(api: WalletApi) -> None:
    account = await api.create_account()

    response = await api.client.get('/v1/transactions', params={'cursor': 'garbage'}, headers=account.headers)

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'invalid_cursor'
