"""Base entity module.

This module defines the base entity class and common types used across
all business entities in the wallet service. It provides foundational
functionality for entity identification and timestamps.
"""

import datetime

from typing import TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field


__all__ = (
    'EntityID',
    'BaseEntity',
    'utc_now',
)


EntityID = TypeVar('EntityID', bound=str)
"""Type variable for entity identifiers.

A generic type variable constrained to string types, used for
strongly typing entity identifiers across the application.
"""


def utc_now() -> datetime.datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.datetime.now(datetime.UTC)


class BaseEntity(BaseModel):
    """Base class for all business entities.

    Provides common functionality for all entities including:
    - Unique identifier generation using UUID4
    - Automatic timestamp tracking for creation and updates
    - Pydantic model validation and serialization

    All domain entities should inherit from this class to ensure
    consistent identity and audit trail capabilities.

    Attributes:
        ID: Unique identifier string generated using UUID4
        created_at: Timestamp when the entity was created (UTC)
        updated_at: Timestamp when the entity was last modified (UTC)
    """

    ID: str = Field(default_factory=lambda: str(uuid4()), description='Unique ID')
    created_at: datetime.datetime = Field(default_factory=utc_now, description='Date and time of creation')
    updated_at: datetime.datetime = Field(default_factory=utc_now, description='Date and time of update')

    def touch(self) -> None:
        """Refresh the update timestamp after a state change."""
        self.updated_at = utc_now()
