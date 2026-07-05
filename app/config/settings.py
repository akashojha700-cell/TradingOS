"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import APP_NAME
from app.version import VERSION

Environment = Literal["development", "staging", "production", "test"]


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    # --- Application metadata ---------------------------------------------
    app_name:    str = Field(default=APP_NAME, alias="APP_NAME")
    app_version: str = Field(default=VERSION,  alias="APP_VERSION")
    app_env:     Environment = Field(default="development", alias="APP_ENV")
    app_debug:   bool = Field(default=True, alias="APP_DEBUG")
    app_host:    str  = Field(default="0.0.0.0", alias="APP_HOST")
    app_port:    int  = Field(default=8000,      alias="APP_PORT")

    # --- Database ---------------------------------------------------------
    database_url: str = Field(default="sqlite:///./storage/tradingos.db", alias="DATABASE_URL")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    # --- Logging ----------------------------------------------------------
    log_level: str  = Field(default="INFO",  alias="LOG_LEVEL")
    log_json:  bool = Field(default=False,   alias="LOG_JSON")

    # --- CORS -------------------------------------------------------------
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")

    # --- Ingest -----------------------------------------------------------
    tradingview_webhook_secret: str | None = Field(default=None, alias="TRADINGVIEW_WEBHOOK_SECRET")

    # --- AI ---------------------------------------------------------------
    ai_provider: str = Field(default="mock", alias="AI_PROVIDER")

    ollama_host:  str = Field(default="http://host.docker.internal:11434", alias="OLLAMA_HOST")
    ollama_model: str = Field(default="qwen3:8b",                          alias="OLLAMA_MODEL")

    # Ollama HTTP timeout (seconds). Accepts either OLLAMA_TIMEOUT (canonical,
    # short) or OLLAMA_TIMEOUT_SECONDS (long form, kept for back-compat).
    # This is the value passed straight to httpx.Client(timeout=...) inside
    # OllamaProvider — the exact number of seconds we'll wait for the model.
    ollama_timeout_seconds: float = Field(
        default=300.0,
        validation_alias=AliasChoices("OLLAMA_TIMEOUT", "OLLAMA_TIMEOUT_SECONDS"),
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        case_sensitive=False, extra="ignore",
        populate_by_name=True,   # allow field-name access via env too
    )

    # ------------------------------------------------------------------ helpers
    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.cors_allow_origins.strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
