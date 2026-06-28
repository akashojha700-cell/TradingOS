"""Root endpoint — ``GET /``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import SystemServiceDep
from app.core.constants import TAG_SYSTEM
from app.schemas import RootResponse

router = APIRouter(tags=[TAG_SYSTEM])


@router.get(
    "/",
    response_model=RootResponse,
    summary="Service banner",
    description="Returns application metadata and a link to the API docs.",
)
def read_root(service: SystemServiceDep) -> RootResponse:
    """Return basic service metadata."""
    return service.root()
