"""FastAPI error handlers for consistent error responses.

This module provides centralized error handling for the FastAPI application,
ensuring consistent error response formats across all endpoints. It handles
application-specific errors, request validation errors, framework HTTP errors
and unexpected exceptions, rendering all of them as:

    {"error": {"code": "...", "message": "...", "details": {...}}}
"""

import logging

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import BaseError


__all__ = (
    'error_response',
    'base_error_handler',
    'validation_error_handler',
    'http_exception_handler',
    'unhandled_error_handler',
    'ERROR_HANDLERS',
)

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES = {
    400: 'bad_request',
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    405: 'method_not_allowed',
    409: 'conflict',
    422: 'validation_error',
    429: 'rate_limit_exceeded',
}


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build a JSON response in the unified error format.

    Args:
        status_code: HTTP status code of the response
        code: Stable machine-readable error code
        message: Human-readable error description
        details: Additional structured information about the error
        headers: Extra HTTP headers to attach to the response

    Returns:
        JSONResponse with the unified error body
    """
    return JSONResponse(
        {
            'error': {
                'code': code,
                'message': message,
                'details': details or {},
            },
        },
        status_code=status_code,
        headers=headers,
    )


async def base_error_handler(_: Request, exc: BaseError) -> JSONResponse:
    """Handle application-specific BaseError exceptions.

    Args:
        _: FastAPI request instance (unused)
        exc: BaseError exception instance with error details

    Returns:
        JSONResponse with structured error information
    """
    return error_response(exc.code, exc.error_code, exc.message, exc.details, exc.headers or None)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors raised by FastAPI/Pydantic.

    Args:
        _: FastAPI request instance (unused)
        exc: Validation error with the list of failed fields

    Returns:
        JSONResponse with status 422 and per-field error details
    """
    errors = [
        {
            'loc': list(error.get('loc', ())),
            'message': error.get('msg', ''),
            'type': error.get('type', ''),
        }
        for error in exc.errors()
    ]
    return error_response(422, 'validation_error', 'Request validation failed', {'errors': jsonable_encoder(errors)})


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle framework-level HTTP exceptions (unknown routes, wrong methods, etc.).

    Args:
        _: FastAPI request instance (unused)
        exc: Starlette HTTP exception

    Returns:
        JSONResponse in the unified error format
    """
    code = HTTP_ERROR_CODES.get(exc.status_code, 'http_error')
    return error_response(exc.status_code, code, str(exc.detail), headers=getattr(exc, 'headers', None))


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions without leaking internals to clients.

    Args:
        _: FastAPI request instance (unused)
        exc: Unhandled exception

    Returns:
        JSONResponse with status 500
    """
    logger.exception('Unhandled error', exc_info=exc)
    return error_response(500, 'internal_error', 'Internal server error')


ERROR_HANDLERS: dict[int | type[Exception], Callable[[Request, Any], Coroutine[Any, Any, Response]]] = {
    BaseError: base_error_handler,
    RequestValidationError: validation_error_handler,
    StarletteHTTPException: http_exception_handler,
    Exception: unhandled_error_handler,
}
"""Mapping of exception types to their corresponding error handlers.

This dictionary is used by FastAPI to automatically route exceptions
to the appropriate handler functions for consistent error responses.
"""
