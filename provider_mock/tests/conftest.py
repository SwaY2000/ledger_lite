"""Shared pytest fixtures for the provider mock."""

import os


os.environ.update(
    {
        'ENV': 'test',
        'PROVIDER_API_KEY': 'test-provider-key',
        'PROVIDER_WEBHOOK_SECRET': 'test-webhook-secret',
        'PROVIDER_PUBLIC_URL': 'http://provider.test',
    },
)

# ruff: noqa: E402 - environment must be configured before the application is imported
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from dependency_injector import providers

from src.asgi import build_app


class RecordingClient:
    """IAsyncClient stub recording webhook deliveries."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    async def post(self, url: str, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        self.requests.append({'url': url, **kwargs})
        return 200, {}

    async def get(self, url: str, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError


@pytest.fixture
def container() -> Any:
    app = build_app()
    return app.state.container


@pytest.fixture
def recorder(container: Any) -> RecordingClient:
    recorder = RecordingClient()
    container.api_client.override(providers.Object(recorder))
    return recorder


@pytest.fixture
async def client(container: Any) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=container.app())
    async with httpx.AsyncClient(
        transport=transport,
        base_url='http://provider.test',
        headers={'Authorization': 'Bearer test-provider-key'},
    ) as http_client:
        yield http_client
