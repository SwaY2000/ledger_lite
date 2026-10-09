"""Repository, mapper and unit of work interfaces.

This module defines the contracts for data access patterns in the wallet
service. Use cases depend only on these protocols; concrete PostgreSQL
implementations live in ``src.repositories.postgres``.
"""

import datetime

from types import TracebackType
from typing import Protocol, Self, TypeVar

from src.entities.account import AccountEntity
from src.entities.deposit import DepositEntity
from src.entities.idempotency import IdempotencyRecordEntity
from src.entities.transaction import TransactionEntity
from src.entities.webhook_event import WebhookEventEntity


# Type variables for generic mapper
TEntity = TypeVar('TEntity')
TModel = TypeVar('TModel')

__all__ = (
    'IMapper',
    'IAccountRepository',
    'IDepositRepository',
    'ITransactionRepository',
    'IIdempotencyRepository',
    'IWebhookEventRepository',
    'IUnitOfWork',
)


class IMapper[TEntity, TModel](Protocol):
    """Generic mapper protocol for entity-model conversion.

    Provides a contract for converting between domain entities and persistence
    layer models, keeping business logic independent of the ORM.

    Type Parameters:
        TEntity: The domain entity type (business logic objects)
        TModel: The persistence model type (storage layer objects)
    """

    def to_model(self, entity: TEntity) -> TModel:
        """Convert a domain entity to a persistence model.

        Args:
            entity: The domain entity to convert

        Returns:
            The corresponding persistence model object
        """

    def to_entity(self, model: TModel) -> TEntity:
        """Convert a persistence model to a domain entity.

        Args:
            model: The persistence model to convert

        Returns:
            The corresponding domain entity object
        """


class IAccountRepository(Protocol):
    """Repository interface for account data access."""

    async def create(self, account: AccountEntity) -> AccountEntity:
        """Persist a new account.

        Args:
            account: Account entity to persist

        Returns:
            The created account entity
        """

    async def get_by_id(self, account_id: str) -> AccountEntity | None:
        """Retrieve an account by its identifier.

        Args:
            account_id: Account identifier

        Returns:
            Account entity if found, None otherwise
        """

    async def get_by_api_key_hash(self, api_key_hash: str) -> AccountEntity | None:
        """Retrieve an account by the hash of its API key.

        Args:
            api_key_hash: SHA-256 hash of the API key

        Returns:
            Account entity if found, None otherwise
        """

    async def lock_many(self, account_ids: list[str]) -> dict[str, AccountEntity]:
        """Lock accounts for update (``SELECT ... FOR UPDATE``) in a deterministic order.

        Locks are taken in ascending id order to avoid deadlocks between
        concurrent transfers in opposite directions.

        Args:
            account_ids: Identifiers of accounts to lock

        Returns:
            Mapping of account id to locked entity (missing ids are absent)
        """

    async def update(self, account: AccountEntity) -> AccountEntity:
        """Persist changes of an existing account.

        Args:
            account: Account entity with updated data

        Returns:
            The updated account entity
        """


class IDepositRepository(Protocol):
    """Repository interface for deposit data access."""

    async def create(self, deposit: DepositEntity) -> DepositEntity:
        """Persist a new deposit."""

    async def get_by_id(self, deposit_id: str) -> DepositEntity | None:
        """Retrieve a deposit by its identifier."""

    async def get_by_invoice_id_for_update(self, invoice_id: str) -> DepositEntity | None:
        """Retrieve and lock a deposit by its provider invoice identifier.

        Args:
            invoice_id: Provider invoice identifier

        Returns:
            Locked deposit entity if found, None otherwise
        """

    async def list_pending_ids_older_than(self, older_than: datetime.datetime, limit: int) -> list[str]:
        """List identifiers of pending deposits created before the given time.

        Args:
            older_than: Upper bound for the creation time
            limit: Maximum number of identifiers to return

        Returns:
            Deposit identifiers ordered by creation time
        """

    async def update(self, deposit: DepositEntity) -> DepositEntity:
        """Persist changes of an existing deposit."""


class ITransactionRepository(Protocol):
    """Repository interface for ledger transactions."""

    async def create(self, transaction: TransactionEntity) -> TransactionEntity:
        """Persist a new ledger transaction."""

    async def list_by_account(
        self,
        account_id: str,
        limit: int,
        before: tuple[datetime.datetime, str] | None = None,
    ) -> list[TransactionEntity]:
        """List account transactions, newest first, using keyset pagination.

        Args:
            account_id: Account identifier
            limit: Maximum number of transactions to return
            before: Exclusive (created_at, id) position to continue after

        Returns:
            Ledger transactions ordered by (created_at, id) descending
        """


class IIdempotencyRepository(Protocol):
    """Repository interface for idempotency records."""

    async def try_create(self, record: IdempotencyRecordEntity) -> bool:
        """Insert a record unless the (account_id, key) pair already exists.

        A concurrent insert of the same key blocks on the unique index until
        the other transaction finishes, which serializes duplicate requests.

        Args:
            record: Idempotency record to insert

        Returns:
            True if the record was inserted, False if the key already exists
        """

    async def get(self, account_id: str, key: str) -> IdempotencyRecordEntity | None:
        """Retrieve a record by account and key."""

    async def update(self, record: IdempotencyRecordEntity) -> IdempotencyRecordEntity:
        """Persist the stored response of a record."""


class IWebhookEventRepository(Protocol):
    """Repository interface for processed provider webhook events."""

    async def try_create(self, event: WebhookEventEntity) -> bool:
        """Insert an event unless an event with the same ``event_id`` exists.

        Args:
            event: Webhook event to insert

        Returns:
            True if the event is new, False if it was already processed
        """


class IUnitOfWork(Protocol):
    """Unit of work: a single database transaction spanning all repositories.

    Usage:
        async with uow:
            account = ...
            await uow.commit()

    Leaving the context without ``commit`` (or with an exception) rolls back.
    """

    accounts: IAccountRepository
    deposits: IDepositRepository
    transactions: ITransactionRepository
    idempotency: IIdempotencyRepository
    webhook_events: IWebhookEventRepository

    async def __aenter__(self) -> Self:
        """Open a new session and transaction."""

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Roll back uncommitted changes and close the session."""

    async def commit(self) -> None:
        """Commit the current transaction."""

    async def rollback(self) -> None:
        """Roll back the current transaction."""
