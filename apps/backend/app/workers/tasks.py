from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from datetime import datetime, timezone
from threading import Lock

from app.core.settings import settings
from app.services.ingest import poll_quotes, warm_candles
from app.services.tile_engine import refresh_symbol
from app.workers.celery_app import app

_LOOP: asyncio.AbstractEventLoop | None = None
_LOOP_LOCK = Lock()
TASK_STAGGER_SECONDS = 0.25


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _LOOP
    if _LOOP is None or _LOOP.is_closed():
        with _LOOP_LOCK:
            if _LOOP is None or _LOOP.is_closed():
                _LOOP = asyncio.new_event_loop()
                asyncio.set_event_loop(_LOOP)
    return _LOOP


def _run_async(coro: Awaitable[None]) -> None:
    loop = _get_worker_loop()
    loop.run_until_complete(coro)


async def _ingest_candles() -> None:
    for ticker in settings.watchlist:
        await warm_candles(ticker)
        await asyncio.sleep(TASK_STAGGER_SECONDS)


async def _poll_options() -> None:
    for ticker in settings.watchlist:
        await poll_quotes(ticker)
        await asyncio.sleep(TASK_STAGGER_SECONDS)


async def _refresh_watchlist() -> None:
    for ticker in settings.watchlist:
        await refresh_symbol(ticker)


@app.task(name="app.workers.tasks.refresh_watchlist")
def refresh_watchlist() -> str:
    _run_async(_refresh_watchlist())
    return datetime.now(timezone.utc).isoformat()


@app.task(name="app.workers.tasks.ingest_candles")
def ingest_candles() -> str:
    _run_async(_ingest_candles())
    return datetime.now(timezone.utc).isoformat()


@app.task(name="app.workers.tasks.poll_options")
def poll_options() -> str:
    _run_async(_poll_options())
    return datetime.now(timezone.utc).isoformat()
