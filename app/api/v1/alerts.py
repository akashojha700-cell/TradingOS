"""Alert read endpoints.

* ``GET /alerts``           — paginated list of ingested alerts.
* ``GET /alerts/{alert_id}`` — fetch a single alert by id.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import AlertServiceDep
from app.core.constants import TAG_ALERTS
from app.schemas.alert import AlertListOut, AlertOut
from app.services.alert_service import AlertNotFoundError

router = APIRouter(prefix="/alerts", tags=[TAG_ALERTS])


@router.get(
    "",
    response_model=AlertListOut,
    summary="List ingested alerts",
    description=(
        "Return a paginated list of stored alerts, newest first. Supports "
        "filtering by `ticker` and `source`."
    ),
)
def list_alerts(
    service: AlertServiceDep,
    limit: int = Query(default=50, ge=1, le=200, description="Page size."),
    offset: int = Query(default=0, ge=0, description="Row offset."),
    ticker: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
        description="Filter by ticker (case-insensitive).",
    ),
    source: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
        description="Filter by source identifier.",
    ),
) -> AlertListOut:
    """Return a page of alerts plus the total count for the same filters."""
    items, total = service.list(
        limit=limit, offset=offset, ticker=ticker, source=source
    )
    return AlertListOut(
        items=[AlertOut.model_validate(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertOut,
    summary="Fetch one alert by id",
    responses={404: {"description": "Alert not found"}},
)
def get_alert(alert_id: int, service: AlertServiceDep) -> AlertOut:
    """Return a single alert, or 404 if it does not exist."""
    try:
        alert = service.get(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    return AlertOut.model_validate(alert)
