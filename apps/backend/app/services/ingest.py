from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from tenacity import retry, stop_after_attempt, wait_fixed

from app.adapters.massive import MassiveClient
from app.core.settings import settings
from app.db.models import Candle, Levels, OptionSnapshot
from app.db.session import async_session
from app.services.data_cache import quote_cache

logger = logging.getLogger(__name__)
CANDLE_TIMEFRAME = "1m"
CANDLE_RETENTION_HOURS = 24
OPTION_RETENTION_MINUTES = 45
_API_WARNING_EMITTED = False


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_ts(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        # Massive returns ms since epoch
        divisor = 1000 if value > 10**11 else 1
        return datetime.fromtimestamp(value / divisor, tz=timezone.utc)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        with suppress(ValueError):
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def _normalize_quote(payload: dict[str, Any]) -> dict[str, Any]:
    bid = _to_float(payload.get("bid"))
    ask = _to_float(payload.get("ask"))
    mid = _to_float(payload.get("mid"))
    if mid is None and bid is not None and ask is not None:
        mid = round((bid + ask) / 2, 4)
    spread = payload.get("spread_pct_of_mid")
    if spread is None and mid and bid is not None and ask is not None and mid != 0:
        spread = round(((ask - bid) / mid) * 100, 4)
    return {
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_pct_of_mid": spread,
        "nbbo_quality": payload.get("nbbo_quality", "unknown"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _quote_status() -> bool:
    global _API_WARNING_EMITTED
    if not settings.massive_api_key:
        if not _API_WARNING_EMITTED:
            logger.warning("massive-api-key-missing; ingestion disabled")
            _API_WARNING_EMITTED = True
        return False
    return True


async def _persist_candles(ticker: str, candles: Iterable[dict[str, Any]] | None) -> None:
    docs = list(candles or [])
    if not docs:
        return
    rows: list[dict[str, Any]] = []
    for doc in docs[-180:]:
        ts = _coerce_ts(doc.get("t"))
        if not ts:
            continue
        rows.append(
            {
                "ticker": ticker,
                "timeframe": CANDLE_TIMEFRAME,
                "ts": ts,
                "open": _to_float(doc.get("o")) or 0.0,
                "high": _to_float(doc.get("h")) or 0.0,
                "low": _to_float(doc.get("l")) or 0.0,
                "close": _to_float(doc.get("c")) or 0.0,
                "volume": int(doc.get("v") or 0),
            }
        )
    if not rows:
        return
    async with async_session() as session:
        stmt = insert(Candle).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Candle.ticker, Candle.timeframe, Candle.ts],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
            },
        )
        await session.execute(stmt)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=CANDLE_RETENTION_HOURS)
        await session.execute(
            delete(Candle).where(Candle.ticker == ticker, Candle.timeframe == CANDLE_TIMEFRAME, Candle.ts < cutoff)
        )
        await session.commit()


async def _upsert_levels(ticker: str, prev_close: dict | None, premarket: dict | None, day: date) -> None:
    prev = ((prev_close or {}).get("results") or [{}])[0]
    payload = {
        "day": day,
        "ticker": ticker,
        "premarket_high": _to_float((premarket or {}).get("preMarketHigh")),
        "premarket_low": _to_float((premarket or {}).get("preMarketLow")),
        "prior_high": _to_float(prev.get("h")),
        "prior_low": _to_float(prev.get("l")),
        "prior_close": _to_float(prev.get("c")),
        "open_print": _to_float(prev.get("o")),
    }
    async with async_session() as session:
        stmt = insert(Levels).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Levels.day, Levels.ticker],
            set_={
                "premarket_high": stmt.excluded.premarket_high,
                "premarket_low": stmt.excluded.premarket_low,
                "prior_high": stmt.excluded.prior_high,
                "prior_low": stmt.excluded.prior_low,
                "prior_close": stmt.excluded.prior_close,
                "open_print": stmt.excluded.open_print,
            },
        )
        await session.execute(stmt)
        await session.commit()


async def _persist_option_snapshots(ticker: str, options: list[dict[str, Any]] | None, ts: datetime) -> None:
    docs = list(options or [])
    if not docs:
        return
    rows: list[dict[str, Any]] = []
    for doc in docs[:80]:
        contract = doc.get("contract")
        if not contract:
            continue
        bid = _to_float(doc.get("bid"))
        ask = _to_float(doc.get("ask"))
        mid = _to_float(doc.get("mid"))
        if mid is None and bid is not None and ask is not None:
            mid = round((bid + ask) / 2, 4)
        rows.append(
            {
                "ticker": ticker,
                "ts": ts,
                "contract": contract,
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "oi": int(doc.get("oi") or 0) if doc.get("oi") is not None else None,
                "vol": int(doc.get("volume") or 0) if doc.get("volume") is not None else None,
                "iv": _to_float(doc.get("iv")),
                "delta": _to_float(doc.get("delta")),
                "gamma": _to_float(doc.get("gamma")),
                "theta": _to_float(doc.get("theta")),
                "vega": _to_float(doc.get("vega")),
            }
        )
    if not rows:
        return
    async with async_session() as session:
        await session.execute(insert(OptionSnapshot).values(rows))
        cutoff = ts - timedelta(minutes=OPTION_RETENTION_MINUTES)
        await session.execute(delete(OptionSnapshot).where(OptionSnapshot.ticker == ticker, OptionSnapshot.ts < cutoff))
        await session.commit()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def warm_candles(ticker: str) -> None:
    ticker = ticker.upper()
    if not _quote_status():
        return
    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(hours=2)
    try:
        async with MassiveClient() as client:
            candles_task = asyncio.create_task(client.get_aggregates(ticker, "minute", window_start, window_end))
            prev_task = asyncio.create_task(client.get_previous_close(ticker))
            premarket_task = asyncio.create_task(client.get_premarket_range(ticker, window_end))
            candles, prev_close, premarket = await asyncio.gather(candles_task, prev_task, premarket_task)
    except Exception as exc:  # pragma: no cover - network path
        logger.warning("warm-candles-fetch-failed", extra={"ticker": ticker, "error": str(exc)})
        return
    await _persist_candles(ticker, candles)
    await _upsert_levels(ticker, prev_close, premarket, window_end.date())
    logger.info("warm-candles", extra={"ticker": ticker, "points": len(candles or [])})


async def poll_quotes(ticker: str) -> None:
    ticker = ticker.upper()
    if not _quote_status():
        return
    now = datetime.now(timezone.utc)
    try:
        async with MassiveClient() as client:
            quote_task = asyncio.create_task(client.get_quote_snapshot(ticker))
            options_task = (
                asyncio.create_task(client.get_options_chain(ticker, now)) if settings.options_data_enabled else None
            )
            quote = await quote_task
            options_chain = await options_task if options_task else []
    except Exception as exc:  # pragma: no cover - network path
        logger.warning("poll-quotes-fetch-failed", extra={"ticker": ticker, "error": str(exc)})
        return
    if quote:
        await quote_cache.set_quote(ticker, _normalize_quote(quote))
    if options_chain:
        await _persist_option_snapshots(ticker, options_chain, now)
    logger.debug("poll-quotes", extra={"ticker": ticker, "contracts": len(options_chain or [])})
