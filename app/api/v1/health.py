"""Health endpoint — ``GET /health``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import DBSessionDep, SystemServiceDep
from app.core.constants import TAG_SYSTEM
from app.schemas import HealthResponse

router = APIRouter(tags=[TAG_SYSTEM])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness & dependency health",
    description=(
        "Returns the overall service status along with the result of a "
        "lightweight database probe."
    ),
)
def read_health(service: SystemServiceDep, db: DBSessionDep) -> HealthResponse:
    """Probe the database and return the resulting health summary."""
    return service.health(db=db)
