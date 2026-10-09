"""Dependency injection and application lifespan management.

This module provides the Lifespan class for managing FastAPI application
lifecycle with dependency injection containers. It handles resource
initialization and cleanup during application startup and shutdown.

The lifespan manager integrates with dependency-injector containers
to ensure proper resource management in production deployments.
"""

from collections.abc import AsyncGenerator
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any

from dependency_injector.containers import Container
from fastapi import FastAPI


__all__ = ('Lifespan',)


class Lifespan:
    """FastAPI application lifespan manager with dependency injection.

    Manages the complete lifecycle of FastAPI applications by coordinating
    with dependency injection containers for resource initialization and
    cleanup. Ensures proper startup and shutdown sequences for databases,
    caches, message brokers, and other external resources.

    The lifespan manager implements both async context manager protocol
    and FastAPI lifespan function protocol for flexible usage patterns.
    """

    def __init__(self, container: Container) -> None:
        """Initialize the lifespan manager with a dependency injection container.

        Args:
            container: Dependency injection container managing application resources
        """
        self.container = container

    async def __aenter__(self) -> None:
        """Async context manager entry - initialize container resources.

        Initializes all resources managed by the dependency injection container
        including database connections, cache pools, and message brokers.
        """
        result = self.container.init_resources()

        if result is not None:
            await result

    async def __aexit__(self, *exc_info: Any) -> None:
        """Async context manager exit - cleanup container resources.

        Gracefully shuts down all resources managed by the dependency injection
        container, ensuring proper cleanup of connections and external resources.

        Args:
            *exc_info: Exception information if context exited due to exception
        """
        result = self.container.shutdown_resources()

        if result is not None:
            await result

    def __call__(self, app: FastAPI) -> _AsyncGeneratorContextManager[None]:
        """FastAPI lifespan context manager factory.

        Creates an async generator that FastAPI uses for application lifespan
        management. This method implements the FastAPI lifespan protocol.

        Args:
            app: FastAPI application instance

        Returns:
            Async generator for FastAPI lifespan management
        """
        return self._lifespan_context(app)

    @asynccontextmanager
    async def _lifespan_context(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """Internal lifespan context manager implementation.

        Handles the actual resource initialization and cleanup sequence
        for FastAPI application lifecycle management.

        Args:
            app: FastAPI application instance

        Yields:
            None: Control to FastAPI application during normal operation
        """
        # Startup
        result = self.container.init_resources()
        if result is not None:
            await result

        try:
            yield
        finally:
            # Shutdown
            result = self.container.shutdown_resources()
            if result is not None:
                await result
