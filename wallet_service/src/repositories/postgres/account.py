"""PostgreSQL repository implementation for account entities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.account import AccountEntity
from src.infrastructure.postgres.models import AccountModel
from src.repositories.interfaces import IMapper


__all__ = ('SqlAlchemyAccountRepository',)


class SqlAlchemyAccountRepository:
    """PostgreSQL implementation of the account repository.

    Operates on the session owned by the unit of work, so all changes
    become visible only after the unit of work commits.
    """

    def __init__(self, session: AsyncSession, mapper: IMapper[AccountEntity, AccountModel]) -> None:
        """Initialize the repository with a session and entity mapper.

        Args:
            session: SQLAlchemy async session of the current unit of work
            mapper: Bidirectional mapper for entity-model conversion
        """
        self._session = session
        self._mapper = mapper

    async def create(self, account: AccountEntity) -> AccountEntity:
        """Persist a new account."""
        self._session.add(self._mapper.to_model(account))
        await self._session.flush()
        return account

    async def get_by_id(self, account_id: str) -> AccountEntity | None:
        """Retrieve an account by its identifier."""
        model = await self._session.get(AccountModel, account_id)
        return self._mapper.to_entity(model) if model else None

    async def get_by_api_key_hash(self, api_key_hash: str) -> AccountEntity | None:
        """Retrieve an account by the hash of its API key."""
        model = await self._session.scalar(select(AccountModel).where(AccountModel.api_key_hash == api_key_hash))
        return self._mapper.to_entity(model) if model else None

    async def lock_many(self, account_ids: list[str]) -> dict[str, AccountEntity]:
        """Lock accounts with ``SELECT ... FOR NO KEY UPDATE`` in ascending id order.

        ``FOR NO KEY UPDATE`` (not ``FOR UPDATE``) is used because inserting rows that reference
        the account (ledger, idempotency keys) takes ``FOR KEY SHARE`` locks; upgrading those to
        ``FOR UPDATE`` deadlocks concurrent transfers, while ``NO KEY UPDATE`` does not conflict.
        """
        result = await self._session.scalars(
            select(AccountModel)
            .where(AccountModel.id.in_(sorted(set(account_ids))))
            .order_by(AccountModel.id)
            .with_for_update(key_share=True)
            .execution_options(populate_existing=True),
        )
        return {model.id: self._mapper.to_entity(model) for model in result}

    async def update(self, account: AccountEntity) -> AccountEntity:
        """Persist changes of an existing account."""
        await self._session.merge(self._mapper.to_model(account))
        await self._session.flush()
        return account
