"""PostgreSQL repository implementation for processed webhook events."""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.webhook_event import WebhookEventEntity
from src.infrastructure.postgres.models import WebhookEventModel
from src.repositories.interfaces import IMapper


__all__ = ('SqlAlchemyWebhookEventRepository',)


class SqlAlchemyWebhookEventRepository:
    """PostgreSQL implementation of the webhook event repository."""

    def __init__(self, session: AsyncSession, mapper: IMapper[WebhookEventEntity, WebhookEventModel]) -> None:
        """Initialize the repository with a session and entity mapper.

        Args:
            session: SQLAlchemy async session of the current unit of work
            mapper: Bidirectional mapper for entity-model conversion
        """
        self._session = session
        self._mapper = mapper

    async def try_create(self, event: WebhookEventEntity) -> bool:
        """Insert an event with ``ON CONFLICT DO NOTHING`` on ``event_id``."""
        model = self._mapper.to_model(event)
        inserted_id = await self._session.scalar(
            insert(WebhookEventModel)
            .values(
                id=model.id,
                event_id=model.event_id,
                invoice_id=model.invoice_id,
                status=model.status,
                paid_amount=model.paid_amount,
                occurred_at=model.occurred_at,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            .on_conflict_do_nothing(index_elements=['event_id'])
            .returning(WebhookEventModel.id),
        )
        return inserted_id is not None
