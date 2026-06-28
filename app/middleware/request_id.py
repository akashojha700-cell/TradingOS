"""Request-ID middleware.

Assigns a stable correlation ID to every incoming request and binds it to the
``structlog`` context so all log lines emitted while handling the request can
be grouped together. The ID is also echoed back to the client via the
``X-Request-ID`` response header.
"""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.constants import HEADER_REQUEST_ID

REQUEST_ID_HEADER = HEADER_REQUEST_ID


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID to each request/response and to log context."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Bind a request ID for the duration of the request."""
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()

        response.headers[REQUEST_ID_HEADER] = request_id
        return response
