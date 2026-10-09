"""PostgreSQL repository implementation for idempotency records."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.idempotency import IdempotencyRecordEntity
from src.infrastructure.postgres.models import IdempotencyKeyModel
from src.repositories.interfaces import IMapper


__all__ = ('SqlAlchemyIdempotencyRepository',)


class SqlAlchemyIdempotencyRepository:
    """PostgreSQL implementation of the idempotency record repository."""

    def __init__(self, session: AsyncSession, mapper: IMapper[IdempotencyRecordEntity, IdempotencyKeyModel]) -> None:
        """Initialize the repository with a session and entity mapper.

        Args:
            session: SQLAlchemy async session of the current unit of work
            mapper: Bidirectional mapper for entity-model conversion
        """
        self._session = session
        self._mapper = mapper

    async def try_create(self, record: IdempotencyRecordEntity) -> bool:
        """Insert a record with ``ON CONFLICT DO NOTHING`` on (account_id, key)."""
        model = self._mapper.to_model(record)
        inserted_id = await self._session.scalar(
            insert(IdempotencyKeyModel)
            .values(
                id=model.id,
                account_id=model.account_id,
                key=model.key,
                request_hash=model.request_hash,
                response_status=model.response_status,
                response_body=model.response_body,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            .on_conflict_do_nothing(index_elements=['account_id', 'key'])
            .returning(IdempotencyKeyModel.id),
        )
        return inserted_id is not None

    async def get(self, account_id: str, key: str) -> IdempotencyRecordEntity | None:
        """Retrieve a record by account and key."""
        model = await self._session.scalar(
            select(IdempotencyKeyModel)
            .where(IdempotencyKeyModel.account_id == account_id, IdempotencyKeyModel.key == key)
            .execution_options(populate_existing=True),
        )
        return self._mapper.to_entity(model) if model else None

    async def update(self, record: IdempotencyRecordEntity) -> IdempotencyRecordEntity:
        """Persist the stored response of a record."""
        await self._session.merge(self._mapper.to_model(record))
        await self._session.flush()
        return record
