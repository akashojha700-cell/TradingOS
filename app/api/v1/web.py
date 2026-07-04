"""Web UI route — serves the TradingOS single-page application at ``/``.

The SPA is a self-contained HTML file under ``app/web/index.html`` that
loads React, Tailwind, and Chart.js from CDNs and talks to the same origin
via ``/api/v1/...``. No build step, no bundler, no npm.

Design decisions recorded in ``docs/ADR/ADR-009-Single-File-SPA.md``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

from app.core.constants import TAG_SYSTEM

router = APIRouter(tags=[TAG_SYSTEM])

# Resolve the HTML file once at import time. Read fresh on each request so
# developers can edit the SPA and see changes on refresh (no server reload).
_INDEX_PATH: Path = Path(__file__).resolve().parents[2] / "web" / "index.html"


@router.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
    summary="TradingOS web application",
    description=(
        "Serves the TradingOS user interface. Developers can still hit "
        "`/api/v1/info` for the JSON service banner and `/docs` for the "
        "OpenAPI explorer."
    ),
)
def read_ui() -> Response:
    """Return the SPA index HTML."""
    if not _INDEX_PATH.exists():  # pragma: no cover - deployment error
        return HTMLResponse(
            content=(
                "<!doctype html><meta charset=utf-8><title>TradingOS</title>"
                "<h1>UI asset missing</h1>"
                "<p>Expected file <code>app/web/index.html</code>.</p>"
            ),
            status_code=500,
        )
    return HTMLResponse(content=_INDEX_PATH.read_text(encoding="utf-8"))
