"""PostgreSQL repository implementation for deposit entities."""

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.deposit import DepositEntity, DepositStatuses
from src.infrastructure.postgres.models import DepositModel
from src.repositories.interfaces import IMapper


__all__ = ('SqlAlchemyDepositRepository',)


class SqlAlchemyDepositRepository:
    """PostgreSQL implementation of the deposit repository."""

    def __init__(self, session: AsyncSession, mapper: IMapper[DepositEntity, DepositModel]) -> None:
        """Initialize the repository with a session and entity mapper.

        Args:
            session: SQLAlchemy async session of the current unit of work
            mapper: Bidirectional mapper for entity-model conversion
        """
        self._session = session
        self._mapper = mapper

    async def create(self, deposit: DepositEntity) -> DepositEntity:
        """Persist a new deposit."""
        self._session.add(self._mapper.to_model(deposit))
        await self._session.flush()
        return deposit

    async def get_by_id(self, deposit_id: str) -> DepositEntity | None:
        """Retrieve a deposit by its identifier."""
        model = await self._session.get(DepositModel, deposit_id)
        return self._mapper.to_entity(model) if model else None

    async def get_by_invoice_id_for_update(self, invoice_id: str) -> DepositEntity | None:
        """Retrieve and lock a deposit by its provider invoice identifier."""
        model = await self._session.scalar(
            select(DepositModel)
            .where(DepositModel.invoice_id == invoice_id)
            .with_for_update(key_share=True)
            .execution_options(populate_existing=True),
        )
        return self._mapper.to_entity(model) if model else None

    async def list_pending_ids_older_than(self, older_than: datetime.datetime, limit: int) -> list[str]:
        """List identifiers of pending deposits with an invoice created before the given time."""
        result = await self._session.scalars(
            select(DepositModel.id)
            .where(
                DepositModel.status == DepositStatuses.PENDING.value,
                DepositModel.invoice_id.is_not(None),
                DepositModel.created_at < older_than,
            )
            .order_by(DepositModel.created_at)
            .limit(limit),
        )
        return list(result)

    async def update(self, deposit: DepositEntity) -> DepositEntity:
        """Persist changes of an existing deposit."""
        await self._session.merge(self._mapper.to_model(deposit))
        await self._session.flush()
        return deposit
