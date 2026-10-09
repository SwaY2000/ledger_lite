"""FastAPI application factory and configuration."""

from fastapi import FastAPI
from starlette.responses import JSONResponse

from src.presentation.rest.routes.invoices import router as invoices_router

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
        Configured FastAPI application instance
    """
    app = FastAPI(
        debug=debug,
        lifespan=lifespan,
        title='LedgerLite Payment Provider Mock',
        description='In-memory payment provider with signed webhooks',
        version='1.0.0',
        exception_handlers=ERROR_HANDLERS,
    )

    @app.get('/health-check/')
    async def health_check() -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({'status': 'ok'})

    app.include_router(invoices_router)

    return app
