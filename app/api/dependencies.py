"""Reusable FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.repositories.alert_repository import AlertRepository
from app.services import SystemService
from app.services.ai import AIProvider, get_ai_provider
from app.services.alert_service import AlertService

# ---- Foundational deps ---------------------------------------------------
SettingsDep = Annotated[Settings, Depends(get_settings)]
"""Resolved application settings."""

DBSessionDep = Annotated[Session, Depends(get_db)]
"""Per-request database session."""


def get_system_service(settings: SettingsDep) -> SystemService:
    """Provide a :class:`SystemService` wired with the current settings."""
    return SystemService(settings=settings)


SystemServiceDep = Annotated[SystemService, Depends(get_system_service)]
"""Convenience alias used by system routers."""


# ---- AI provider deps ----------------------------------------------------
def _get_ai_provider(settings: SettingsDep) -> AIProvider:
    """Resolve the concrete :class:`AIProvider` from configuration."""
    return get_ai_provider(settings)


AIProviderDep = Annotated[AIProvider, Depends(_get_ai_provider)]


# ---- Alert deps ----------------------------------------------------------
def get_alert_repository(db: DBSessionDep) -> AlertRepository:
    """Provide an :class:`AlertRepository` bound to the request's DB session."""
    return AlertRepository(db=db)


AlertRepoDep = Annotated[AlertRepository, Depends(get_alert_repository)]


def get_alert_service(
    repo: AlertRepoDep,
    ai: AIProviderDep,
) -> AlertService:
    """Provide an :class:`AlertService` wired with a repo and an AI provider."""
    return AlertService(repo=repo, ai=ai)


AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
"""Convenience alias used by alert routers."""
