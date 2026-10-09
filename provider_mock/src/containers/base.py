"""Base dependency injection container."""

from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Provider

from src.entities.invoice import InvoiceEntity
from src.infrastructure.api_client import AsyncHTTPXApiClient, IAsyncClient
from src.repositories.interfaces import IInvoiceRepository
from src.repositories.memory import InMemoryInvoiceRepository
from src.services.webhook_sender import IWebhookSenderService, WebhookSenderService
from src.use_cases.create_invoice import CreateInvoiceUseCase
from src.use_cases.dtos import (
    CreateInvoiceInput,
    CreateInvoiceOutput,
    GetInvoiceInput,
    SimulateInvoiceInput,
    SimulateInvoiceOutput,
)
from src.use_cases.get_invoice import GetInvoiceUseCase
from src.use_cases.interfaces import IUseCase
from src.use_cases.simulate_invoice import SimulateInvoiceUseCase


__all__ = ('Container',)


class Container(DeclarativeContainer):
    """Base dependency injection container of the provider mock."""

    config = providers.Configuration(strict=True)

    # infrastructure
    api_client: Provider[IAsyncClient] = providers.Factory(
        AsyncHTTPXApiClient,
        timeout=config.webhook_timeout_seconds,
    )

    # repositories
    invoice_repository: Provider[IInvoiceRepository] = providers.Singleton(
        InMemoryInvoiceRepository,
    )

    # services
    webhook_sender_service: Provider[IWebhookSenderService] = providers.Factory(
        WebhookSenderService,
        api_client=api_client,
        secret=config.provider_webhook_secret,
    )

    # use cases
    create_invoice_use_case: Provider[IUseCase[CreateInvoiceInput, CreateInvoiceOutput]] = providers.Factory(
        CreateInvoiceUseCase,
        invoice_repository=invoice_repository,
        public_url=config.provider_public_url,
    )
    get_invoice_use_case: Provider[IUseCase[GetInvoiceInput, InvoiceEntity]] = providers.Factory(
        GetInvoiceUseCase,
        invoice_repository=invoice_repository,
    )
    simulate_invoice_use_case: Provider[IUseCase[SimulateInvoiceInput, SimulateInvoiceOutput]] = providers.Factory(
        SimulateInvoiceUseCase,
        invoice_repository=invoice_repository,
        webhook_sender_service=webhook_sender_service,
    )
