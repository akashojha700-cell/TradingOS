"""TradingView webhook ingest — ``POST /webhook/tradingview``.

Accepts a JSON payload posted by a TradingView alert, validates it, persists
it as an :class:`~app.models.alert.Alert`, and returns 202 Accepted with the
new alert id.

An optional shared secret may be configured via
``TRADINGVIEW_WEBHOOK_SECRET``. When set, callers must include the
``X-Webhook-Secret`` header with the matching value.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.dependencies import AlertServiceDep, SettingsDep
from app.core.constants import HEADER_WEBHOOK_SECRET, TAG_WEBHOOKS
from app.schemas.alert import AlertCreated, TradingViewAlertIn

router = APIRouter(prefix="/webhook", tags=[TAG_WEBHOOKS])


def verify_webhook_secret(
    settings: SettingsDep,
    x_webhook_secret: str | None = Header(default=None, alias=HEADER_WEBHOOK_SECRET),
) -> None:
    """Gate the webhook on an optional shared secret.

    When the env var is unset the webhook is open (development default).
    When the env var is set, the caller must supply the matching header value.
    """
    expected = settings.tradingview_webhook_secret
    if expected:
        if not x_webhook_secret or x_webhook_secret != expected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing webhook secret",
            )


@router.post(
    "/tradingview",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AlertCreated,
    summary="Ingest a TradingView alert",
    description=(
        "Accept a TradingView alert payload, validate the required fields "
        "(`ticker`, `action`), persist the full payload as an Alert, and "
        "return 202 Accepted with the new alert id."
    ),
    dependencies=[Depends(verify_webhook_secret)],
)
async def receive_tradingview_alert(
    payload: TradingViewAlertIn,
    request: Request,
    service: AlertServiceDep,
) -> AlertCreated:
    """Validate, persist, and acknowledge a TradingView alert."""
    # ``payload`` has already been validated by FastAPI; pull the raw dict so
    # we can preserve any extra fields the user included in their template.
    raw: dict = await request.json()
    alert = service.ingest_tradingview(raw_payload=raw, parsed=payload)
    return AlertCreated(id=alert.id, received_at=alert.received_at)
