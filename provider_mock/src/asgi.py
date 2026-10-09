"""ASGI application builder and configuration."""

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
    """Build and configure the ASGI FastAPI application for deployment."""
    container = bootstrap_('web')

    logging.basicConfig(level=logging.INFO)
    logging.getLogger('uvicorn.access').addFilter(ByRouteNameFilter(filter_routes=['/health-check']))

    app = container.app()
    app.state.container = container
    return app
