"""PostgreSQL storage implementation for async database operations.

This module provides the PostgresDatabase class that manages the async
SQLAlchemy engine and session factory used by the unit of work.
"""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


__all__ = (
    'PostgresDatabase',
    'init_postgres_database',
)


class PostgresDatabase:
    """Async PostgreSQL connection manager.

    Owns the SQLAlchemy async engine (connection pool) and the session factory.
    The engine is created lazily by SQLAlchemy, so constructing this class
    performs no I/O; ``connect`` verifies connectivity explicitly.

    Attributes:
        _engine: SQLAlchemy async engine
        _session_factory: Factory producing new AsyncSession instances
    """

    def __init__(self, url: str, pool_size: int = 10, max_overflow: int = 20, echo: bool = False) -> None:
        """Initialize PostgreSQL engine configuration.

        Args:
            url: SQLAlchemy database URL (``postgresql+asyncpg://...``)
            pool_size: Number of persistent connections in the pool
            max_overflow: Number of extra connections allowed above pool_size
            echo: Log all SQL statements
        """
        self._engine: AsyncEngine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            echo=echo,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, autoflush=False)

    @property
    def engine(self) -> AsyncEngine:
        """SQLAlchemy async engine."""
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Factory producing new AsyncSession instances."""
        return self._session_factory

    async def connect(self) -> None:
        """Verify database connectivity.

        Raises:
            OperationalError: If the database is unreachable
        """
        async with self._engine.connect() as connection:
            await connection.execute(text('SELECT 1'))

    async def disconnect(self) -> None:
        """Close all pooled connections."""
        await self._engine.dispose()


async def init_postgres_database(database: PostgresDatabase) -> AsyncIterator[PostgresDatabase]:
    """Resource initializer managing the database lifecycle in the DI container.

    Args:
        database: Database instance to manage

    Yields:
        The connected database instance
    """
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()
