"""Web container for REST API dependencies.

This module defines the WebContainer class that extends the base Container
with web-specific dependencies like FastAPI application instance and
lifespan management.
"""

from dependency_injector.providers import Factory, Self, Singleton

from src.app_factory import create_app
from src.di import Lifespan

from .base import Container


__all__ = ('WebContainer',)


class WebContainer(Container):
    """Dependency injection container for web/API applications.

    Extends the base Container with web-specific dependencies:
    - FastAPI application instance
    - Application lifespan management
    - Self-reference for dependency injection
    """

    __self__ = Self()
    lifespan = Singleton(Lifespan, __self__)

    app = Factory(
        create_app,
        lifespan,
        Container.config.debug,
    )
