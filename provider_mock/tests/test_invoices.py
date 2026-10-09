"""Provider mock: invoices, final statuses and signed webhooks."""

import hashlib
import hmac
import json

from typing import Any

import httpx

from tests.conftest import RecordingClient


async def _create(client: httpx.AsyncClient, amount: str = '10.00') -> dict[str, Any]:
    response = await client.post(
        '/invoices',
        json={'amount': amount, 'currency': 'USD', 'external_id': 'dep_1', 'callback_url': 'http://wallet/hook'},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_and_get_invoice(client: httpx.AsyncClient) -> None:
    created = await _create(client)

    assert created['status'] == 'pending'
    assert created['invoice_id'].startswith('inv_')
    assert created['pay_url'] == f'http://provider.test/pay/{created["invoice_id"]}'

    response = await client.get(f'/invoices/{created["invoice_id"]}')
    assert response.json()['status'] == 'pending'
    assert response.json()['paid_amount'] == '0.00'


async def test_requires_bearer_token(client: httpx.AsyncClient) -> None:
    response = await client.get('/invoices/inv_x', headers={'Authorization': 'Bearer wrong'})

    assert response.status_code == 401
    assert response.json()['error']['code'] == 'unauthorized'


async def test_simulate_sends_signed_webhook(client: httpx.AsyncClient, recorder: RecordingClient) -> None:
    created = await _create(client)

    response = await client.post(f'/invoices/{created["invoice_id"]}/simulate', json={'status': 'paid'})

    assert response.status_code == 200
    assert response.json()['paid_amount'] == '10.00'
    [request] = recorder.requests
    assert request['url'] == 'http://wallet/hook'
    body = request['content']
    timestamp = request['headers']['X-Timestamp']
    expected = hmac.new(b'test-webhook-secret', f'{timestamp}.'.encode() + body, hashlib.sha256).hexdigest()
    assert request['headers']['X-Signature'] == f'sha256={expected}'
    payload = json.loads(body)
    assert payload['invoice_id'] == created['invoice_id']
    assert payload['status'] == 'paid'
    assert payload['paid_amount'] == '10.00'
    assert payload['event_id'] == response.json()['event_id']


async def test_duplicate_sends_same_event_twice(client: httpx.AsyncClient, recorder: RecordingClient) -> None:
    created = await _create(client)

    await client.post(
        f'/invoices/{created["invoice_id"]}/simulate',
        json={'status': 'partially_paid', 'paid_amount': '7.50', 'duplicate': True},
    )

    assert len(recorder.requests) == 2
    events = [json.loads(r['content']) for r in recorder.requests]
    assert events[0] == events[1]
    assert events[0]['paid_amount'] == '7.50'


async def test_final_status_never_changes(client: httpx.AsyncClient, recorder: RecordingClient) -> None:
    created = await _create(client)
    url = f'/invoices/{created["invoice_id"]}/simulate'

    await client.post(url, json={'status': 'expired'})
    response = await client.post(url, json={'status': 'paid'})

    assert response.status_code == 409
    assert response.json()['error']['code'] == 'invoice_already_final'
    assert (await client.get(f'/invoices/{created["invoice_id"]}')).json()['status'] == 'expired'


async def test_deliver_webhook_false_does_not_send(client: httpx.AsyncClient, recorder: RecordingClient) -> None:
    created = await _create(client)

    await client.post(f'/invoices/{created["invoice_id"]}/simulate', json={'status': 'paid', 'deliver_webhook': False})

    assert recorder.requests == []


async def test_validation_errors(client: httpx.AsyncClient) -> None:
    created = await _create(client)

    as_number = await client.post(
        '/invoices',
        json={'amount': 10.0, 'currency': 'USD', 'external_id': 'x', 'callback_url': 'http://x'},
    )
    partial_without_amount = await client.post(
        f'/invoices/{created["invoice_id"]}/simulate',
        json={'status': 'partially_paid'},
    )

    assert as_number.status_code == 422
    assert partial_without_amount.status_code == 422
    assert partial_without_amount.json()['error']['code'] == 'validation_error'
