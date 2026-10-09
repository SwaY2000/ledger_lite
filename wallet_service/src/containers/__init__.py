"""Dependency injection containers module.

This module provides the bootstrap function and container classes for dependency
injection in the wallet service. It supports base (CLI) and web containers.
"""

from typing import Literal

from dependency_injector.containers import DeclarativeContainer

from src.config.app import config


__all__ = ('bootstrap',)


def bootstrap(container_type: Literal['base', 'web'] = 'base') -> DeclarativeContainer:
    """Bootstrap a dependency injection container based on the specified type.

    Args:
        container_type: The type of container to create. Can be 'base' or 'web'.
                       Defaults to 'base'.

    Returns:
        Container: A configured container instance of the appropriate type.
    """
    container: DeclarativeContainer
    if container_type == 'web':
        from .web import WebContainer
        container = WebContainer()
    else:
        from .base import Container
        container = Container()

    container.config.from_dict(config.model_dump(), required=True)

    if container_type == 'web':
        container.wire(
            modules=[
                'src.presentation.rest.auth',
                'src.presentation.rest.rate_limit',
            ],
            packages=[
                'src.presentation.rest.v1.routes',
            ],
        )

    return container
