"""HTTPX-based implementation of async API client.

This module provides a concrete implementation of the async API client
using the HTTPX library for HTTP requests.
"""

import logging

from typing import Any

import httpx

from httpx import HTTPError, TimeoutException

from .base import BaseAsyncApiClient


__all__ = ('AsyncHTTPXApiClient',)

logger = logging.getLogger(__name__)


class AsyncHTTPXApiClient(BaseAsyncApiClient):
    """Async HTTP API client implementation using HTTPX library.

    This client creates a new HTTPX AsyncClient for each request.

    Example:
        client = AsyncHTTPXApiClient(timeout=5)
        status, data = await client.post(
            "https://api.example.com/users",
            data={"name": "John", "email": "john@example.com"}
        )
    """

    @staticmethod
    async def _make_request(method: str, /, **kwargs) -> httpx.Response:
        """Make an HTTP request using HTTPX.

        Args:
            method: HTTP method name (get, post)
            **kwargs: Arguments to pass to the HTTPX request method

        Returns:
            The HTTP response object

        Raises:
            HTTPError: If the request fails
            TimeoutException: If the request times out
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                return await getattr(client, method)(**kwargs)
        except TimeoutException as e:
            logger.error(f'Request timeout for {method.upper()} {kwargs.get("url")}: {e!r}')
            raise
        except HTTPError as e:
            logger.error(f'HTTP error for {method.upper()} {kwargs.get("url")}: {e!r}')
            raise

    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: httpx.Timeout | None = None,  # noqa: ASYNC109
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any] | list[Any]]:
        """Make an HTTP POST request with JSON data.

        Args:
            url: The URL to send the request to
            params: URL query parameters
            data: JSON data to send in the request body
            headers: HTTP headers to include in the request
            timeout: Request timeout (uses default if not specified)
            **kwargs: Additional arguments passed to HTTPX

        Returns:
            Tuple of (status_code, response_data)

        Raises:
            HTTPError: If the request fails
            TimeoutException: If the request times out
        """
        logger.debug(f'POST request to {url}')
        return self._handle_response(
            await self._make_request(
                'post',
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=timeout or self.timeout,
                **kwargs,
            ),
        )

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: httpx.Timeout | None = None,  # noqa: ASYNC109
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any] | list[Any]]:
        """Make an HTTP GET request.

        Args:
            url: The URL to send the request to
            params: URL query parameters
            headers: HTTP headers to include in the request
            timeout: Request timeout (uses default if not specified)
            **kwargs: Additional arguments passed to HTTPX

        Returns:
            Tuple of (status_code, response_data)

        Raises:
            HTTPError: If the request fails
            TimeoutException: If the request times out
        """
        logger.debug(f'GET request to {url}')
        return self._handle_response(
            await self._make_request(
                'get',
                url=url,
                params=params,
                headers=headers,
                timeout=timeout or self.timeout,
                **kwargs,
            ),
        )
