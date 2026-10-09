"""Base interfaces and classes for async HTTP API clients.

This module provides abstract base classes for building async HTTP clients
with consistent interface across different HTTP library implementations.
"""

import abc
import logging

from json import JSONDecodeError
from typing import Any

from httpx import Response, Timeout


__all__ = (
    'IAsyncClient',
    'BaseAsyncApiClient',
)

logger = logging.getLogger(__name__)


class IAsyncClient(metaclass=abc.ABCMeta):
    """Abstract base class for async HTTP clients.

    This interface defines standard HTTP methods for async API clients.
    Implementations should handle HTTP requests, response parsing, and error handling.
    """

    @abc.abstractmethod
    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: Timeout | None = None,  # noqa: ASYNC109
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any] | list[Any]]:
        """Make an HTTP POST request.

        Args:
            url: The URL to send the request to
            params: URL query parameters
            data: JSON data to send in the request body
            headers: HTTP headers to include in the request
            timeout: Request timeout configuration
            **kwargs: Additional arguments passed to the underlying HTTP client

        Returns:
            Tuple of (status_code, response_data) where response_data is parsed JSON

        Raises:
            HTTPError: If the request fails
            TimeoutException: If the request times out
        """

    @abc.abstractmethod
    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: Timeout | None = None,  # noqa: ASYNC109
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any] | list[Any]]:
        """Make an HTTP GET request.

        Args:
            url: The URL to send the request to
            params: URL query parameters
            headers: HTTP headers to include in the request
            timeout: Request timeout configuration
            **kwargs: Additional arguments passed to the underlying HTTP client

        Returns:
            Tuple of (status_code, response_data) where response_data is parsed JSON

        Raises:
            HTTPError: If the request fails
            TimeoutException: If the request times out
        """


class BaseAsyncApiClient(IAsyncClient, abc.ABC):
    """Base implementation of async API client with common functionality.

    Provides default timeout configuration and response handling logic.
    Subclasses should implement the actual HTTP request methods.

    Attributes:
        timeout: Default timeout for all requests
    """

    timeout: Timeout = Timeout(10.0)

    def __init__(self, timeout: float | None = None) -> None:
        """Initialize the client.

        Args:
            timeout: Default timeout in seconds for every request (connect, read, write, pool)
        """
        if timeout is not None:
            self.timeout = Timeout(timeout)

    @staticmethod
    def _handle_response(
        response: Response,
    ) -> tuple[int, dict[str, Any] | list[Any]]:
        """Handle HTTP response and parse JSON content.

        Args:
            response: The HTTP response object

        Returns:
            Tuple of (status_code, parsed_json_data)

        Note:
            If JSON parsing fails, returns an empty dict instead of raising an error.
        """
        try:
            return response.status_code, response.json()
        except JSONDecodeError as e:
            logger.warning(
                f'Failed to decode JSON response from {response.url}: {e}. Status: {response.status_code}',
            )
            return response.status_code, {}
