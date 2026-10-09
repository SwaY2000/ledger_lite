"""FastAPI application factory and configuration.

This module provides the factory function for creating and configuring
the FastAPI application instance. It handles route registration, error
handling, and application lifecycle management.
"""

from fastapi import FastAPI
from starlette.responses import JSONResponse

from src.presentation.rest.v1.routes.accounts import router as accounts_router
from src.presentation.rest.v1.routes.deposits import router as deposits_router
from src.presentation.rest.v1.routes.purchases import router as purchases_router
from src.presentation.rest.v1.routes.transactions import router as transactions_router
from src.presentation.rest.v1.routes.transfers import router as transfers_router
from src.presentation.rest.v1.routes.webhooks import router as webhooks_router

from .di import Lifespan
from .error_handlers import ERROR_HANDLERS


__all__ = ('create_app',)


def create_app(
    lifespan: Lifespan,
    debug: bool = False,
) -> FastAPI:
    """Create and configure the FastAPI application instance.

    Args:
        lifespan: Dependency injection lifespan manager for resource management
        debug: Enable debug mode for development (default: False)

    Returns:
        Configured FastAPI application instance ready for deployment

    Features:
        - Versioned API structure (/v1/...)
        - Health check endpoint (/health-check/)
        - Unified error format for every endpoint
        - Dependency injection integration
    """
    main_app = FastAPI(
        debug=debug,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        exception_handlers=ERROR_HANDLERS,
    )

    @main_app.get('/health-check/')
    async def health_check() -> JSONResponse:
        """Health check endpoint for monitoring and container orchestration.

        Returns:
            JSONResponse with status indicator
        """
        return JSONResponse({'status': 'ok'})

    # v1 api
    v1_app = FastAPI(
        debug=debug,
        title='LedgerLite Wallet API V1',
        description='USD wallets with provider deposits, idempotent transfers and credit purchases',
        version='1.0.0',
        exception_handlers=ERROR_HANDLERS,
    )
    v1_app.include_router(accounts_router)
    v1_app.include_router(deposits_router)
    v1_app.include_router(webhooks_router)
    v1_app.include_router(transfers_router)
    v1_app.include_router(purchases_router)
    v1_app.include_router(transactions_router)

    main_app.mount('/v1', v1_app)

    return main_app
