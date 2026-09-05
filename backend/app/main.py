"""Revenue Autopsy - Application Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import actions, health, incidents, outcomes
from app.core.config import settings
from app.core.errors import register_exception_handlers


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        docs_url="/docs" if settings.APP_ENV == "development" else None,
        redoc_url="/redoc" if settings.APP_ENV == "development" else None,
    )

    # CORS Middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # Centralized exception handlers
    register_exception_handlers(app)

    # Mount health endpoint at root /health and versioned /api/v1/health
    app.include_router(health.router)
    app.include_router(health.router, prefix="/api/v1")

    # Mount versioned domain API routers
    app.include_router(incidents.router, prefix="/api/v1")
    app.include_router(actions.router, prefix="/api/v1")
    app.include_router(outcomes.router, prefix="/api/v1")

    return app


app = create_application()
