"""Shared pytest fixtures.

Integration tests run the real FastAPI application in-process against a
real PostgreSQL database (``TEST_DATABASE_URL``). The payment provider is
replaced through the DI container with an in-memory fake.
"""

import os


TEST_DATABASE_URL = os.environ.get(
    'TEST_DATABASE_URL',
    'postgresql+asyncpg://ledgerlite:change-me@localhost:5432/ledgerlite_test',
)
WEBHOOK_SECRET = 'test-webhook-secret'

os.environ.update(
    {
        'ENV': 'test',
        'DATABASE_URL': TEST_DATABASE_URL,
        'PROVIDER_BASE_URL': 'http://provider.test',
        'PROVIDER_API_KEY': 'test-provider-key',
        'PROVIDER_WEBHOOK_SECRET': WEBHOOK_SECRET,
        'PROVIDER_TIMEOUT_SECONDS': '1',
        'WALLET_CALLBACK_URL': 'http://wallet.test/v1/webhooks/provider',
        'RATE_LIMIT_PER_MINUTE': '1000',
    },
)

# ruff: noqa: E402 - environment must be configured before the application is imported
from collections.abc import AsyncIterator
from typing import Any

import asyncpg
import httpx
import pytest

from dependency_injector import providers
from sqlalchemy import text
from sqlalchemy.engine import make_url

from src.asgi import build_app
from src.infrastructure.postgres.models import Base
from src.infrastructure.rate_limiter import InMemoryRateLimiter

from .fakes import FakePaymentProvider
from .helpers import WalletApi


async def _ensure_database_exists() -> None:
    """Create the test database if it does not exist yet."""
    url = make_url(TEST_DATABASE_URL)
    connection = await asyncpg.connect(
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port or 5432,
        database='postgres',
    )
    try:
        exists = await connection.fetchval('SELECT 1 FROM pg_database WHERE datname = $1', url.database)
        if not exists:
            await connection.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await connection.close()


@pytest.fixture(scope='session')
async def container() -> AsyncIterator[Any]:
    """Application DI container with a freshly created schema."""
    await _ensure_database_exists()

    app = build_app()
    container = app.state.container

    engine = container.postgres_database().engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield container

    await container.postgres_database().disconnect()


@pytest.fixture
def fake_provider(container: Any) -> FakePaymentProvider:
    """In-memory payment provider injected into the container."""
    fake = FakePaymentProvider()
    container.payment_provider_service.override(providers.Object(fake))
    return fake


@pytest.fixture(autouse=True)
async def clean_state(request: pytest.FixtureRequest) -> AsyncIterator[None]:
    """Truncate tables and reset container overrides around every integration test."""
    if 'integration' not in str(request.path):
        yield
        return

    container = request.getfixturevalue('container')
    tables = ', '.join(table.name for table in Base.metadata.sorted_tables)
    async with container.postgres_database().engine.begin() as connection:
        await connection.execute(text(f'TRUNCATE {tables} CASCADE'))

    container.rate_limiter.override(providers.Object(InMemoryRateLimiter(limit=1000)))
    yield
    container.payment_provider_service.reset_override()
    container.rate_limiter.reset_override()


@pytest.fixture
async def client(container: Any) -> AsyncIterator[httpx.AsyncClient]:
    """HTTP client calling the application in-process."""
    transport = httpx.ASGITransport(app=container.app())
    async with httpx.AsyncClient(transport=transport, base_url='http://wallet.test') as http_client:
        yield http_client


@pytest.fixture
def api(client: httpx.AsyncClient, container: Any) -> WalletApi:
    """High-level helper for calling the wallet API in tests."""
    return WalletApi(client=client, container=container, webhook_secret=WEBHOOK_SECRET)
