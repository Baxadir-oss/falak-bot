"""
Butun ilova uchun markazlashgan konfiguratsiya.
Hech qayerda "qattiq yozilgan" (hardcoded) qiymat bo'lmasligi kerak —
hammasi shu yerdan, .env fayldan o'qiladi.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Telegram ---
    bot_token: str
    webhook_base_url: str
    webhook_path: str = "/webhook"
    webhook_secret: str

    # --- Server ---
    host: str = "127.0.0.1"
    port: int = 8080

    # --- Database ---
    db_path: str = "./data/falak.db"

    # --- Open-Meteo ---
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"

    # --- Cache ---
    cache_ttl_seconds: int = 1800
    cache_max_size: int = 2000

    # --- CORS ---
    cors_origins: str = ""

    # --- Log ---
    log_level: str = "INFO"

    @property
    def webhook_url(self) -> str:
        return self.webhook_base_url.rstrip("/") + self.webhook_path

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
