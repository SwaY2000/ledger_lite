"""ASGI application builder and configuration.

This module provides the ASGI application builder function that creates
and configures the FastAPI application for deployment. It handles container
bootstrapping, logging configuration and application initialization.
"""

import logging

from collections.abc import Callable
from typing import Literal

from dependency_injector.containers import DeclarativeContainer
from fastapi import FastAPI

from src.presentation.rest.log_filters import ByRouteNameFilter

from .containers import bootstrap


__all__ = ('build_app',)


def build_app(
    bootstrap_: Callable[[Literal['base', 'web']], DeclarativeContainer] = bootstrap,
) -> FastAPI:
    """Build and configure the ASGI FastAPI application for deployment.

    Args:
        bootstrap_: Container bootstrap function (default: bootstrap from containers)

    Returns:
        Fully configured FastAPI application ready for ASGI deployment
    """
    container = bootstrap_('web')

    logging.basicConfig(level=logging.INFO)
    logging.getLogger('uvicorn.access').addFilter(ByRouteNameFilter(filter_routes=['/health-check']))

    app = container.app()
    app.state.container = container
    return app
