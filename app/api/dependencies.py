"""Reusable FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.repositories.alert_repository import AlertRepository
from app.services import SystemService
from app.services.ai import AIProvider, JsonValidator, PromptBuilder, get_ai_provider
from app.services.alert_service import AlertService
from app.services.analysis_service import AnalysisService
from app.services.market import MarketDataProvider, get_market_provider

# ---- Foundational deps ---------------------------------------------------
SettingsDep  = Annotated[Settings, Depends(get_settings)]
DBSessionDep = Annotated[Session,  Depends(get_db)]


def get_system_service(settings: SettingsDep) -> SystemService:
    return SystemService(settings=settings)


SystemServiceDep = Annotated[SystemService, Depends(get_system_service)]


# ---- Intelligence-layer deps --------------------------------------------
def _get_ai_provider(settings: SettingsDep) -> AIProvider:
    return get_ai_provider(settings)


AIProviderDep = Annotated[AIProvider, Depends(_get_ai_provider)]


def _get_market_provider(settings: SettingsDep) -> MarketDataProvider:
    return get_market_provider(settings)


MarketProviderDep = Annotated[MarketDataProvider, Depends(_get_market_provider)]


def _get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


PromptBuilderDep = Annotated[PromptBuilder, Depends(_get_prompt_builder)]


def _get_json_validator() -> JsonValidator:
    return JsonValidator()


JsonValidatorDep = Annotated[JsonValidator, Depends(_get_json_validator)]


def get_analysis_service(
    market: MarketProviderDep,
    ai: AIProviderDep,
    prompt_builder: PromptBuilderDep,
    validator: JsonValidatorDep,
) -> AnalysisService:
    return AnalysisService(
        market=market, ai=ai, prompt_builder=prompt_builder, validator=validator,
    )


AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]


# ---- Alert deps ----------------------------------------------------------
def get_alert_repository(db: DBSessionDep) -> AlertRepository:
    return AlertRepository(db=db)


AlertRepoDep = Annotated[AlertRepository, Depends(get_alert_repository)]


def get_alert_service(
    repo: AlertRepoDep,
    analysis: AnalysisServiceDep,
) -> AlertService:
    return AlertService(repo=repo, analysis=analysis)


AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
