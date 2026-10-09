"""PostgreSQL repository implementation for ledger transactions."""

import datetime

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.transaction import TransactionEntity
from src.infrastructure.postgres.models import TransactionModel
from src.repositories.interfaces import IMapper


__all__ = ('SqlAlchemyTransactionRepository',)


class SqlAlchemyTransactionRepository:
    """PostgreSQL implementation of the ledger transaction repository."""

    def __init__(self, session: AsyncSession, mapper: IMapper[TransactionEntity, TransactionModel]) -> None:
        """Initialize the repository with a session and entity mapper.

        Args:
            session: SQLAlchemy async session of the current unit of work
            mapper: Bidirectional mapper for entity-model conversion
        """
        self._session = session
        self._mapper = mapper

    async def create(self, transaction: TransactionEntity) -> TransactionEntity:
        """Persist a new ledger transaction."""
        self._session.add(self._mapper.to_model(transaction))
        await self._session.flush()
        return transaction

    async def list_by_account(
        self,
        account_id: str,
        limit: int,
        before: tuple[datetime.datetime, str] | None = None,
    ) -> list[TransactionEntity]:
        """List account transactions, newest first, using keyset pagination."""
        query = select(TransactionModel).where(TransactionModel.account_id == account_id)
        if before is not None:
            query = query.where(tuple_(TransactionModel.created_at, TransactionModel.id) < tuple_(*before))

        result = await self._session.scalars(
            query.order_by(TransactionModel.created_at.desc(), TransactionModel.id.desc()).limit(limit),
        )
        return [self._mapper.to_entity(model) for model in result]
