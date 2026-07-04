"""TradingView webhook ingest — ``POST /api/v1/webhook/tradingview``.

Accepts a JSON payload posted by a TradingView alert, validates it, persists
it, runs the mock/real AI analysis, and returns 201 Created with the new
alert id and the analysis attached.

An optional shared secret may be configured via
``TRADINGVIEW_WEBHOOK_SECRET``. When set, callers must include the
``X-Webhook-Secret`` header with the matching value.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.dependencies import AlertServiceDep, SettingsDep
from app.core.constants import HEADER_WEBHOOK_SECRET, TAG_WEBHOOKS
from app.core.logging import get_logger
from app.schemas.alert import AlertAnalysis, AlertCreated, TradingViewAlertIn

router = APIRouter(prefix="/webhook", tags=[TAG_WEBHOOKS])
logger = get_logger("tradingos.webhook")


def verify_webhook_secret(
    settings: SettingsDep,
    x_webhook_secret: str | None = Header(default=None, alias=HEADER_WEBHOOK_SECRET),
) -> None:
    """Gate the webhook on an optional shared secret."""
    expected = settings.tradingview_webhook_secret
    if expected:
        if not x_webhook_secret or x_webhook_secret != expected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing webhook secret",
            )


@router.post(
    "/tradingview",
    status_code=status.HTTP_201_CREATED,
    response_model=AlertCreated,
    summary="Ingest a TradingView alert",
    description=(
        "Accept a TradingView alert payload, validate the required fields "
        "(`symbol`, `exchange`, `signal`, `price`), persist the full payload "
        "as an Alert, run the AI provider, and return 201 Created with the "
        "new alert id and analysis attached."
    ),
    dependencies=[Depends(verify_webhook_secret)],
    responses={
        201: {"description": "Alert stored and analysed"},
        403: {"description": "Webhook secret missing or invalid"},
        422: {"description": "Payload validation failed"},
    },
)
async def receive_tradingview_alert(
    payload: TradingViewAlertIn,
    request: Request,
    service: AlertServiceDep,
) -> AlertCreated:
    """Validate, persist, analyse, and acknowledge a TradingView alert."""
    logger.info(
        "webhook.received",
        source="tradingview",
        symbol=payload.symbol,
        signal=payload.signal,
    )
    # Payload has already been validated by FastAPI at this point.
    logger.info("webhook.validated", symbol=payload.symbol, signal=payload.signal)

    raw: dict = await request.json()
    alert = service.ingest_tradingview(raw_payload=raw, parsed=payload)

    analysis = AlertAnalysis.model_validate(alert.analysis or {})
    logger.info(
        "webhook.response_returned",
        alert_id=alert.id,
        status=alert.status,
        recommendation=analysis.recommendation,
    )
    return AlertCreated(
        id=alert.id,
        status=alert.status,  # type: ignore[arg-type]
        created_at=alert.created_at,
        analysis=analysis,
    )
