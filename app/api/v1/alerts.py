"""Alert read + delete endpoints.

* ``GET /api/v1/alerts``             — paginated list of ingested alerts.
* ``GET /api/v1/alerts/recent``      — most recent N alerts.
* ``GET /api/v1/alerts/{alert_id}``  — fetch a single alert (with analysis).
* ``DELETE /api/v1/alerts/{alert_id}`` — remove an alert.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status

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
        "filtering by `symbol`, `signal`, `source`, and `status`."
    ),
)
def list_alerts(
    service: AlertServiceDep,
    limit: int = Query(default=50, ge=1, le=200, description="Page size."),
    offset: int = Query(default=0, ge=0, description="Row offset."),
    symbol: str | None = Query(default=None, min_length=1, max_length=50),
    signal: str | None = Query(default=None, min_length=1, max_length=10),
    source: str | None = Query(default=None, min_length=1, max_length=50),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        min_length=1,
        max_length=20,
        description="Filter by lifecycle status.",
    ),
) -> AlertListOut:
    """Return a page of alerts plus the total matching count."""
    items, total = service.list(
        limit=limit,
        offset=offset,
        symbol=symbol,
        signal=signal,
        source=source,
        status=status_filter,
    )
    return AlertListOut(
        items=[AlertOut.model_validate(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/recent",
    response_model=list[AlertOut],
    summary="Most recent alerts",
    description="Return the most recently ingested alerts, newest first.",
)
def get_recent_alerts(
    service: AlertServiceDep,
    limit: int = Query(default=10, ge=1, le=100),
) -> list[AlertOut]:
    """Return the ``limit`` most recent alerts."""
    return [AlertOut.model_validate(a) for a in service.get_recent(limit=limit)]


@router.get(
    "/{alert_id}",
    response_model=AlertOut,
    summary="Fetch one alert by id",
    responses={404: {"description": "Alert not found"}},
)
def get_alert(alert_id: int, service: AlertServiceDep) -> AlertOut:
    """Return a single alert (with analysis), or 404 if it does not exist."""
    try:
        alert = service.get_by_id(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    return AlertOut.model_validate(alert)


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an alert",
    responses={
        204: {"description": "Alert deleted"},
        404: {"description": "Alert not found"},
    },
)
def delete_alert(alert_id: int, service: AlertServiceDep) -> Response:
    """Delete an alert by id."""
    try:
        service.delete(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
