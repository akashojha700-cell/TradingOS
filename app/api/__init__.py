"""HTTP API package.

Routers are grouped by version under :mod:`app.api.v1`. The aggregate
``api_router`` is mounted onto the FastAPI application in
:mod:`app.main`.
"""

from app.api.v1.router import api_router

__all__ = ["api_router"]
