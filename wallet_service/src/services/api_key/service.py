"""API key service implementations.

API keys are random 256-bit tokens. Only their SHA-256 hash is stored, so a
database leak does not reveal usable keys. A fast hash (instead of bcrypt or
argon2) is sufficient here because keys are high-entropy random values, not
user-chosen passwords, and it allows an indexed lookup by hash on every request.
"""

import hashlib
import secrets

from typing import Protocol


__all__ = (
    'IApiKeyService',
    'ApiKeyService',
)


class IApiKeyService(Protocol):
    """Protocol for API key generation and hashing."""

    def generate(self) -> str:
        """Generate a new plain API key."""

    def hash(self, api_key: str) -> str:
        """Hash a plain API key for storage and lookup."""


class ApiKeyService:
    """API key service based on ``secrets`` and SHA-256."""

    prefix = 'll_'

    def generate(self) -> str:
        """Generate a new plain API key.

        Returns:
            Random URL-safe key with the ``ll_`` prefix
        """
        return f'{self.prefix}{secrets.token_urlsafe(32)}'

    def hash(self, api_key: str) -> str:
        """Hash a plain API key.

        Args:
            api_key: Plain API key

        Returns:
            Hex-encoded SHA-256 digest
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
