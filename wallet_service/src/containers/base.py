"""Base dependency injection container.

This module defines the base Container class that provides infrastructure,
mappers, the unit of work, services and use cases of the wallet service.
"""

from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Provider

from src.entities.account import AccountEntity
from src.infrastructure.api_client import AsyncHTTPXApiClient, IAsyncClient
from src.infrastructure.postgres import PostgresDatabase, init_postgres_database
from src.infrastructure.rate_limiter import InMemoryRateLimiter, IRateLimiter
from src.repositories.interfaces import IUnitOfWork
from src.repositories.postgres import SqlAlchemyUnitOfWork
from src.repositories.postgres.mappers import (
    AccountMapper,
    DepositMapper,
    IdempotencyRecordMapper,
    TransactionMapper,
    WebhookEventMapper,
)
from src.services.api_key import ApiKeyService, IApiKeyService
from src.services.deposit_settlement import DepositSettlementService, IDepositSettlementService
from src.services.payment_provider import HttpPaymentProviderService, IPaymentProviderService
from src.services.webhook_verifier import HmacWebhookSignatureVerifier, IWebhookSignatureVerifier
from src.use_cases.authenticate_account import AuthenticateAccountUseCase
from src.use_cases.create_account import CreateAccountUseCase
from src.use_cases.create_deposit import CreateDepositUseCase
from src.use_cases.create_purchase import CreatePurchaseUseCase
from src.use_cases.create_transfer import CreateTransferUseCase
from src.use_cases.dtos import (
    AccountOutput,
    AuthenticateAccountInput,
    CreateAccountInput,
    CreateAccountOutput,
    CreateDepositInput,
    CreatePurchaseInput,
    CreateTransferInput,
    CreateTransferOutput,
    DepositOutput,
    GetAccountInput,
    ListTransactionsInput,
    ListTransactionsOutput,
    ProcessProviderWebhookInput,
    ProcessProviderWebhookOutput,
    PurchaseOutput,
    ReconcileDepositsInput,
    ReconcileDepositsOutput,
)
from src.use_cases.get_account import GetAccountUseCase
from src.use_cases.interfaces import IUseCase
from src.use_cases.list_transactions import ListTransactionsUseCase
from src.use_cases.process_provider_webhook import ProcessProviderWebhookUseCase
from src.use_cases.reconcile_deposits import ReconcileDepositsUseCase


__all__ = ('Container',)


class Container(DeclarativeContainer):
    """Base dependency injection container.

    Provides infrastructure, mappers, the unit of work, services and use cases.
    """

    config = providers.Configuration(strict=True)

    # infrastructure
    postgres_database: Provider[PostgresDatabase] = providers.Singleton(
        PostgresDatabase,
        url=config.database_url,
        pool_size=config.database_pool_size,
        max_overflow=config.database_max_overflow,
        echo=config.database_echo,
    )
    postgres_database_resource = providers.Resource(
        init_postgres_database,
        database=postgres_database,
    )
    api_client: Provider[IAsyncClient] = providers.Factory(
        AsyncHTTPXApiClient,
        timeout=config.provider_timeout_seconds,
    )
    rate_limiter: Provider[IRateLimiter] = providers.Singleton(
        InMemoryRateLimiter,
        limit=config.rate_limit_per_minute,
        window_seconds=config.rate_limit_window_seconds,
    )

    # mappers
    account_mapper = providers.Factory(AccountMapper)
    deposit_mapper = providers.Factory(DepositMapper)
    transaction_mapper = providers.Factory(TransactionMapper)
    idempotency_mapper = providers.Factory(IdempotencyRecordMapper)
    webhook_event_mapper = providers.Factory(WebhookEventMapper)

    # unit of work (repositories are exposed through it)
    unit_of_work: Provider[IUnitOfWork] = providers.Factory(
        SqlAlchemyUnitOfWork,
        session_factory=postgres_database.provided.session_factory,
        account_mapper=account_mapper,
        deposit_mapper=deposit_mapper,
        transaction_mapper=transaction_mapper,
        idempotency_mapper=idempotency_mapper,
        webhook_event_mapper=webhook_event_mapper,
    )

    # services
    api_key_service: Provider[IApiKeyService] = providers.Factory(
        ApiKeyService,
    )
    payment_provider_service: Provider[IPaymentProviderService] = providers.Factory(
        HttpPaymentProviderService,
        api_client=api_client,
        base_url=config.provider_base_url,
        api_key=config.provider_api_key,
    )
    webhook_signature_verifier: Provider[IWebhookSignatureVerifier] = providers.Factory(
        HmacWebhookSignatureVerifier,
        secret=config.provider_webhook_secret,
        tolerance_seconds=config.webhook_tolerance_seconds,
    )
    deposit_settlement_service: Provider[IDepositSettlementService] = providers.Factory(
        DepositSettlementService,
    )

    # use cases
    create_account_use_case: Provider[IUseCase[CreateAccountInput, CreateAccountOutput]] = providers.Factory(
        CreateAccountUseCase,
        uow=unit_of_work,
        api_key_service=api_key_service,
    )
    authenticate_account_use_case: Provider[IUseCase[AuthenticateAccountInput, AccountEntity]] = providers.Factory(
        AuthenticateAccountUseCase,
        uow=unit_of_work,
        api_key_service=api_key_service,
    )
    get_account_use_case: Provider[IUseCase[GetAccountInput, AccountOutput]] = providers.Factory(
        GetAccountUseCase,
        uow=unit_of_work,
    )
    create_deposit_use_case: Provider[IUseCase[CreateDepositInput, DepositOutput]] = providers.Factory(
        CreateDepositUseCase,
        uow=unit_of_work,
        payment_provider_service=payment_provider_service,
        callback_url=config.wallet_callback_url,
    )
    process_provider_webhook_use_case: Provider[IUseCase[ProcessProviderWebhookInput, ProcessProviderWebhookOutput]] = (
        providers.Factory(
            ProcessProviderWebhookUseCase,
            uow=unit_of_work,
            webhook_signature_verifier=webhook_signature_verifier,
            deposit_settlement_service=deposit_settlement_service,
        )
    )
    create_transfer_use_case: Provider[IUseCase[CreateTransferInput, CreateTransferOutput]] = providers.Factory(
        CreateTransferUseCase,
        uow=unit_of_work,
    )
    create_purchase_use_case: Provider[IUseCase[CreatePurchaseInput, PurchaseOutput]] = providers.Factory(
        CreatePurchaseUseCase,
        uow=unit_of_work,
    )
    list_transactions_use_case: Provider[IUseCase[ListTransactionsInput, ListTransactionsOutput]] = providers.Factory(
        ListTransactionsUseCase,
        uow=unit_of_work,
    )
    reconcile_deposits_use_case: Provider[IUseCase[ReconcileDepositsInput, ReconcileDepositsOutput]] = (
        providers.Factory(
            ReconcileDepositsUseCase,
            uow=unit_of_work,
            payment_provider_service=payment_provider_service,
            deposit_settlement_service=deposit_settlement_service,
        )
    )
