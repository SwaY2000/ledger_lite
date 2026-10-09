"""Helpers for integration tests."""

import hashlib
import hmac
import json
import time

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx

from sqlalchemy import text

from src.use_cases.dtos import CreateAccountInput


def sign(body: bytes, secret: str, timestamp: int | None = None) -> dict[str, str]:
    """Build provider webhook signature headers."""
    ts = str(timestamp if timestamp is not None else int(time.time()))
    digest = hmac.new(secret.encode(), ts.encode() + b'.' + body, hashlib.sha256).hexdigest()
    return {'X-Timestamp': ts, 'X-Signature': f'sha256={digest}', 'Content-Type': 'application/json'}


@dataclass
class Account:
    """Test account credentials."""

    id: str
    api_key: str

    @property
    def headers(self) -> dict[str, str]:
        return {'X-API-Key': self.api_key}


@dataclass
class WalletApi:
    """High-level wrapper around the wallet API for tests."""

    client: httpx.AsyncClient
    container: Any
    webhook_secret: str

    async def create_account(self, name: str = 'user', balance: str | None = None) -> Account:
        result = await self.container.create_account_use_case()(CreateAccountInput(name=name))
        account = Account(id=result.account_id, api_key=result.api_key)
        if balance is not None:
            await self.set_balance(account, balance)
        return account

    async def set_balance(self, account: Account, balance: str) -> None:
        async with self.container.postgres_database().engine.begin() as connection:
            await connection.execute(
                text('UPDATE accounts SET balance_usd = :balance WHERE id = :id'),
                {'balance': Decimal(balance), 'id': account.id},
            )

    async def balance(self, account: Account) -> dict[str, Any]:
        response = await self.client.get('/v1/accounts/me', headers=account.headers)
        assert response.status_code == 200, response.text
        return response.json()

    async def deposit(self, account: Account, amount: str = '10.00') -> dict[str, Any]:
        response = await self.client.post('/v1/deposits', json={'amount': amount}, headers=account.headers)
        assert response.status_code == 201, response.text
        return response.json()

    async def webhook(
        self,
        invoice_id: str,
        status: str,
        paid_amount: str | None = None,
        event_id: str | None = None,
        timestamp: int | None = None,
        secret: str | None = None,
    ) -> httpx.Response:
        body = json.dumps(
            {
                'event_id': event_id or f'evt_{uuid4().hex}',
                'invoice_id': invoice_id,
                'status': status,
                'paid_amount': paid_amount,
                'occurred_at': '2026-10-10T10:00:00Z',
            },
        ).encode()
        headers = sign(body, secret or self.webhook_secret, timestamp)
        return await self.client.post('/v1/webhooks/provider', content=body, headers=headers)

    async def transfer(
        self,
        sender: Account,
        to_account_id: str,
        amount: str,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        headers = dict(sender.headers)
        headers['Idempotency-Key'] = idempotency_key or str(uuid4())
        return await self.client.post(
            '/v1/transfers',
            json={'to_account_id': to_account_id, 'amount': amount},
            headers=headers,
        )
