from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.settings import settings

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def verify_api_key(header: str | None = Security(api_key_header)) -> None:
    if not header or header != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def require_watchlist(symbol: str) -> str:
    if symbol.upper() not in settings.watchlist:
        raise HTTPException(status_code=404, detail="Unknown symbol")
    return symbol.upper()
