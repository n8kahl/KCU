from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.settings import settings
from app.services import ingest
from app.workers.celery_app import app


async def _run_for_watchlist(job):
    for ticker in settings.watchlist:
        await job(ticker)


@app.task(name="app.workers.tasks.ingest_candles")
def ingest_candles() -> str:
    asyncio.run(_run_for_watchlist(ingest.warm_candles))
    return datetime.now(timezone.utc).isoformat()


@app.task(name="app.workers.tasks.poll_options")
def poll_options() -> str:
    asyncio.run(_run_for_watchlist(ingest.poll_quotes))
    return datetime.now(timezone.utc).isoformat()
