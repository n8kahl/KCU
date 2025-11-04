from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = Field(default=3001, validation_alias="PORT")
    database_url: str = Field(default="postgresql+asyncpg://localhost/kcu", validation_alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    polygon_api_key: str | None = Field(default=None, validation_alias="POLYGON_API_KEY")
    discord_webhook_url: str | None = Field(default=None, validation_alias="DISCORD_WEBHOOK_URL")
    frontend_origin: str = Field(default="https://kcu-ui-production.up.railway.app", validation_alias="FRONTEND_ORIGIN")
    service_env: str = Field(default="development", validation_alias="SERVICE_ENV")
    api_key: str = Field(default="dev-admin-key", validation_alias="API_KEY")
    watchlist_raw: str = Field(default="SPY,AAPL,MSFT,NVDA,QQQ,TSLA,AMZN,GOOGL", validation_alias="WATCHLIST")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def watchlist(self) -> List[str]:
        return [token.strip().upper() for token in self.watchlist_raw.split(",") if token.strip()]

    @property
    def cors_allowlist(self) -> list[str]:
        return [self.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
