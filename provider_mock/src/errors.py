"""Application-specific exception classes and error definitions.

Errors are rendered in the same unified format as the wallet service:

    {"error": {"code": "...", "message": "...", "details": {...}}}
"""

from typing import Any


__all__ = (
    'BaseError',
    'UnauthorizedError',
    'InvoiceNotFoundError',
    'InvoiceAlreadyFinalError',
    'ValidationError',
)


class BaseError(Exception):
    """Base exception class for all application-specific errors.

    Attributes:
        code: HTTP status code for the error (default: 400)
        message: Human-readable error description
        error_code: Stable machine-readable error code for clients
        details: Additional structured information about the error
        headers: Extra HTTP headers to attach to the error response
    """

    code = 400
    message = 'Something went wrong'
    error_code = 'bad_request'

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None) -> None:
        """Initialize the error with an optional custom message and details."""
        self.message = message or self.message
        self.details: dict[str, Any] = details or {}
        self.headers: dict[str, str] = {}
        super().__init__(self.message)


class UnauthorizedError(BaseError):
    """Missing or invalid bearer token."""

    code = 401
    message = 'Missing or invalid bearer token'
    error_code = 'unauthorized'


class InvoiceNotFoundError(BaseError):
    """Requested invoice does not exist."""

    code = 404
    message = 'Invoice not found'
    error_code = 'invoice_not_found'


class InvoiceAlreadyFinalError(BaseError):
    """Invoice is in a final status and cannot change anymore."""

    code = 409
    message = 'Invoice is already in a final status'
    error_code = 'invoice_already_final'


class ValidationError(BaseError):
    """Request payload is semantically invalid."""

    code = 422
    message = 'Request validation failed'
    error_code = 'validation_error'
