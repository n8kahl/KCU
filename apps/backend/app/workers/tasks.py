from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.settings import settings
from app.services.ingest import poll_quotes, warm_candles
from app.services.tile_engine import refresh_symbol
from app.workers.celery_app import app


async def _ingest_candles() -> None:
    for ticker in settings.watchlist:
        await warm_candles(ticker)


async def _poll_options() -> None:
    for ticker in settings.watchlist:
        await poll_quotes(ticker)


async def _refresh_watchlist() -> None:
    for ticker in settings.watchlist:
        await refresh_symbol(ticker)


@app.task(name="app.workers.tasks.refresh_watchlist")
def refresh_watchlist() -> str:
    asyncio.run(_refresh_watchlist())
    return datetime.now(timezone.utc).isoformat()


@app.task(name="app.workers.tasks.ingest_candles")
def ingest_candles() -> str:
    asyncio.run(_ingest_candles())
    return datetime.now(timezone.utc).isoformat()


@app.task(name="app.workers.tasks.poll_options")
def poll_options() -> str:
    asyncio.run(_poll_options())
    return datetime.now(timezone.utc).isoformat()
