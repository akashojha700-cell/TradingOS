"""Info endpoint — ``GET /api/v1/info``.

Returns the JSON service banner previously served at ``/``. Moved so that
the root URL can serve the human-facing UI instead. Kept for developer /
monitoring use.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import SystemServiceDep
from app.core.constants import TAG_SYSTEM
from app.schemas import RootResponse

router = APIRouter(tags=[TAG_SYSTEM])


@router.get(
    "/info",
    response_model=RootResponse,
    summary="Service banner (JSON)",
    description="Returns application metadata as JSON.",
)
def read_info(service: SystemServiceDep) -> RootResponse:
    """Return basic service metadata."""
    return service.root()
