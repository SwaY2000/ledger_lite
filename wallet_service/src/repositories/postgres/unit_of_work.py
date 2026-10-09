"""SQLAlchemy unit of work implementation.

The unit of work opens one session (and therefore one database transaction)
and exposes all repositories bound to it. Use cases that move money perform
every read-lock-write step inside a single unit of work, so either all
changes are committed or none of them are.
"""

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.entities.account import AccountEntity
from src.entities.deposit import DepositEntity
from src.entities.idempotency import IdempotencyRecordEntity
from src.entities.transaction import TransactionEntity
from src.entities.webhook_event import WebhookEventEntity
from src.infrastructure.postgres.models import (
    AccountModel,
    DepositModel,
    IdempotencyKeyModel,
    TransactionModel,
    WebhookEventModel,
)
from src.repositories.interfaces import IMapper

from .account import SqlAlchemyAccountRepository
from .deposit import SqlAlchemyDepositRepository
from .idempotency import SqlAlchemyIdempotencyRepository
from .transaction import SqlAlchemyTransactionRepository
from .webhook_event import SqlAlchemyWebhookEventRepository


__all__ = ('SqlAlchemyUnitOfWork',)


class SqlAlchemyUnitOfWork:
    """Unit of work backed by a single SQLAlchemy async session.

    The instance can be entered multiple times sequentially (e.g. one
    transaction per reconciled deposit); every ``async with`` opens a
    fresh session.
    """

    accounts: SqlAlchemyAccountRepository
    deposits: SqlAlchemyDepositRepository
    transactions: SqlAlchemyTransactionRepository
    idempotency: SqlAlchemyIdempotencyRepository
    webhook_events: SqlAlchemyWebhookEventRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        account_mapper: IMapper[AccountEntity, AccountModel],
        deposit_mapper: IMapper[DepositEntity, DepositModel],
        transaction_mapper: IMapper[TransactionEntity, TransactionModel],
        idempotency_mapper: IMapper[IdempotencyRecordEntity, IdempotencyKeyModel],
        webhook_event_mapper: IMapper[WebhookEventEntity, WebhookEventModel],
    ) -> None:
        """Initialize the unit of work with a session factory and mappers.

        Args:
            session_factory: Factory producing new AsyncSession instances
            account_mapper: Mapper for accounts
            deposit_mapper: Mapper for deposits
            transaction_mapper: Mapper for ledger transactions
            idempotency_mapper: Mapper for idempotency records
            webhook_event_mapper: Mapper for webhook events
        """
        self._session_factory = session_factory
        self._account_mapper = account_mapper
        self._deposit_mapper = deposit_mapper
        self._transaction_mapper = transaction_mapper
        self._idempotency_mapper = idempotency_mapper
        self._webhook_event_mapper = webhook_event_mapper
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        """Open a new session and bind all repositories to it."""
        session = self._session_factory()
        self._session = session
        self.accounts = SqlAlchemyAccountRepository(session, self._account_mapper)
        self.deposits = SqlAlchemyDepositRepository(session, self._deposit_mapper)
        self.transactions = SqlAlchemyTransactionRepository(session, self._transaction_mapper)
        self.idempotency = SqlAlchemyIdempotencyRepository(session, self._idempotency_mapper)
        self.webhook_events = SqlAlchemyWebhookEventRepository(session, self._webhook_event_mapper)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Roll back uncommitted changes and close the session."""
        if self._session is None:
            return
        try:
            await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> AsyncSession:
        """Current session.

        Raises:
            RuntimeError: If used outside of ``async with``
        """
        if self._session is None:
            raise RuntimeError('Unit of work is not active')
        return self._session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self.session.rollback()
