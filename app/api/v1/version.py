"""Version endpoint — ``GET /version``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import SystemServiceDep
from app.core.constants import TAG_SYSTEM
from app.schemas import VersionResponse

router = APIRouter(tags=[TAG_SYSTEM])


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Application build metadata",
    description="Returns application and runtime version information.",
)
def read_version(service: SystemServiceDep) -> VersionResponse:
    """Return application + runtime version information."""
    return service.version()
