"""TradingOS FastAPI application factory.

This module exposes ``app`` — the ASGI callable consumed by Uvicorn. The
factory function :func:`create_app` is split out so tests can build isolated
application instances if needed.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.core.constants import APP_DESCRIPTION
from app.core.lifespan import lifespan
from app.middleware import RequestIDMiddleware


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Returns:
        A fully-wired :class:`FastAPI` instance, ready to serve requests.
    """
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---- Middleware -----------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestIDMiddleware)

    # ---- Routers --------------------------------------------------------
    application.include_router(api_router)

    return application


# ASGI entrypoint — referenced by uvicorn (``uvicorn app.main:app``) and the
# Dockerfile.
app: FastAPI = create_app()

# Re-export the package version for convenience.
__all__ = ["app", "create_app", "__version__"]
