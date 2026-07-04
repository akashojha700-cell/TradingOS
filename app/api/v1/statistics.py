"""Statistics endpoint — ``GET /api/v1/statistics``.

Small summary payload for the ingest pipeline. Meant for dashboards, smoke
tests, and quick production sanity checks.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import AlertServiceDep
from app.core.constants import TAG_STATISTICS
from app.schemas.alert import StatisticsOut

router = APIRouter(prefix="/statistics", tags=[TAG_STATISTICS])


@router.get(
    "",
    response_model=StatisticsOut,
    summary="Ingest pipeline statistics",
    description=(
        "Return total / BUY / SELL alert counts, the most recent alert, and "
        "the current application version metadata."
    ),
)
def get_statistics(service: AlertServiceDep) -> StatisticsOut:
    """Return summary statistics for the ingest pipeline."""
    return service.statistics()
