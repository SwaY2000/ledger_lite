"""Application-specific exception classes and error definitions.

This module defines the base exception class and error hierarchy for
the wallet service. Every error carries an HTTP status code, a stable
machine-readable error code, a human-readable message and optional details,
which are rendered by the error handlers in a single unified format:

    {"error": {"code": "insufficient_funds", "message": "...", "details": {...}}}
"""

from typing import Any


__all__ = (
    'BaseError',
    'BadRequestError',
    'ValidationError',
    'UnauthorizedError',
    'InvalidSignatureError',
    'NotFoundError',
    'AccountNotFoundError',
    'DepositNotFoundError',
    'ConflictError',
    'InsufficientFundsError',
    'IdempotencyKeyConflictError',
    'IdempotencyKeyRequiredError',
    'InvalidTransferError',
    'InvalidCursorError',
    'RateLimitExceededError',
    'ProviderUnavailableError',
    'ProviderError',
)


class BaseError(Exception):
    """Base exception class for all application-specific errors.

    Provides a consistent error structure with HTTP status codes,
    human-readable messages, stable error codes and optional details.

    Attributes:
        code: HTTP status code for the error (default: 400)
        message: Human-readable error description
        error_code: Stable machine-readable error code for clients
        details: Additional structured information about the error
        headers: Extra HTTP headers to attach to the error response

    Usage:
        Subclass this exception for specific error types and override
        the class attributes with appropriate values for each error case.
    """

    code = 400
    message = 'Something went wrong'
    error_code = 'bad_request'

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None) -> None:
        """Initialize the error with an optional custom message and details.

        Args:
            message: Human-readable message overriding the class default
            details: Additional structured information about the error
        """
        self.message = message or self.message
        self.details: dict[str, Any] = details or {}
        self.headers: dict[str, str] = {}
        super().__init__(self.message)


class BadRequestError(BaseError):
    """Generic malformed request error."""

    code = 400
    message = 'Bad request'
    error_code = 'bad_request'


class ValidationError(BaseError):
    """Request payload failed validation."""

    code = 422
    message = 'Request validation failed'
    error_code = 'validation_error'


class UnauthorizedError(BaseError):
    """Missing or invalid API key."""

    code = 401
    message = 'Missing or invalid API key'
    error_code = 'unauthorized'


class InvalidSignatureError(BaseError):
    """Webhook signature is missing, invalid or expired."""

    code = 401
    message = 'Invalid webhook signature'
    error_code = 'invalid_signature'


class NotFoundError(BaseError):
    """Requested resource does not exist."""

    code = 404
    message = 'Resource not found'
    error_code = 'not_found'


class AccountNotFoundError(NotFoundError):
    """Requested account does not exist."""

    message = 'Account not found'
    error_code = 'account_not_found'


class DepositNotFoundError(NotFoundError):
    """Deposit referenced by the provider does not exist."""

    message = 'Deposit not found'
    error_code = 'deposit_not_found'


class ConflictError(BaseError):
    """Request conflicts with the current state of the resource."""

    code = 409
    message = 'Conflict'
    error_code = 'conflict'


class InsufficientFundsError(ConflictError):
    """Account balance is too low for the requested operation."""

    message = 'Insufficient funds'
    error_code = 'insufficient_funds'


class IdempotencyKeyConflictError(ConflictError):
    """Idempotency key was already used with a different request body."""

    message = 'Idempotency-Key was already used with a different request body'
    error_code = 'idempotency_key_conflict'


class IdempotencyKeyRequiredError(BadRequestError):
    """Idempotency-Key header is missing."""

    message = 'Idempotency-Key header is required'
    error_code = 'idempotency_key_required'


class InvalidTransferError(BadRequestError):
    """Transfer request is semantically invalid (e.g. transfer to self)."""

    message = 'Invalid transfer'
    error_code = 'invalid_transfer'


class InvalidCursorError(BadRequestError):
    """Pagination cursor cannot be decoded."""

    message = 'Invalid pagination cursor'
    error_code = 'invalid_cursor'


class RateLimitExceededError(BaseError):
    """Too many requests for a single API key."""

    code = 429
    message = 'Rate limit exceeded'
    error_code = 'rate_limit_exceeded'

    def __init__(self, retry_after: int, message: str | None = None) -> None:
        """Initialize the error with the number of seconds to wait.

        Args:
            retry_after: Seconds until the client may retry
            message: Optional custom message
        """
        super().__init__(message, details={'retry_after': retry_after})
        self.headers = {'Retry-After': str(retry_after)}


class ProviderUnavailableError(BaseError):
    """Payment provider timed out, is unreachable or returned a 5xx."""

    code = 502
    message = 'Payment provider is unavailable, please retry later'
    error_code = 'provider_unavailable'


class ProviderError(BaseError):
    """Payment provider rejected the request."""

    code = 502
    message = 'Payment provider rejected the request'
    error_code = 'provider_error'
