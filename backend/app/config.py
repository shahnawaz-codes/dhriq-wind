from datetime import date
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Elexon API Configuration
    elexon_base_url: str = Field(
        default="https://data.elexon.co.uk/bmrs/api/v1",
        validation_alias="ELEXON_BASE_URL",
    )
    elexon_timeout_seconds: float = Field(
        default=30.0,
        validation_alias="ELEXON_TIMEOUT_SECONDS",
    )
    elexon_max_retries: int = Field(
        default=3,
        validation_alias="ELEXON_MAX_RETRIES",
    )
    elexon_chunk_days: int = Field(
        default=7,
        validation_alias="ELEXON_CHUNK_DAYS",
    )

    # Delivery Window & Business Rules
    delivery_window_start: date = Field(
        default=date(2026, 1, 1),
        validation_alias="DELIVERY_WINDOW_START",
    )
    delivery_window_end: date = Field(
        default=date(2026, 1, 31),
        validation_alias="DELIVERY_WINDOW_END",
    )
    decision_cutoff_local_time: str = Field(
        default="09:00",
        validation_alias="DECISION_CUTOFF_LOCAL_TIME",
    )
    decision_timezone: str = Field(
        default="Europe/London",
        validation_alias="DECISION_TIMEZONE",
    )
    forecast_publish_lookback_days: int = Field(
        default=2,
        validation_alias="FORECAST_PUBLISH_LOOKBACK_DAYS",
    )

    # Cache & Performance
    cache_ttl_seconds: int = Field(
        default=86400,
        validation_alias="CACHE_TTL_SECONDS",
    )
    preload_on_startup: bool = Field(
        default=True,
        validation_alias="PRELOAD_ON_STARTUP",
    )

    # Server & Security
    cors_allowed_origins: list[str] | str = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
        ],
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    app_version: str = "1.0.0"

    @field_validator("cors_allowed_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(x).strip() for x in v if str(x).strip()]
        return [str(v)]


@lru_cache
def get_settings() -> Settings:
    return Settings()
