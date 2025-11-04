from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.settings import settings
from app.services.tile_engine import refresh_symbol
from app.workers.celery_app import app


async def _refresh_watchlist() -> None:
    for ticker in settings.watchlist:
        await refresh_symbol(ticker)


@app.task(name="app.workers.tasks.refresh_watchlist")
def refresh_watchlist() -> str:
    asyncio.run(_refresh_watchlist())
    return datetime.now(timezone.utc).isoformat()
