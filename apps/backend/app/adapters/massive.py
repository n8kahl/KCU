from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from massive import RESTClient
from massive.exceptions import BadResponse

from app.core.settings import settings


def _parse_error(exc: BadResponse) -> tuple[str | None, str]:
    try:
        payload = json.loads(str(exc))
    except json.JSONDecodeError:
        return None, str(exc)
    status = payload.get("status") or payload.get("error_code")
    message = payload.get("error") or payload.get("message", "")
    return (status.upper() if isinstance(status, str) else None, str(message))


def _is_not_found(exc: BadResponse) -> bool:
    status, message = _parse_error(exc)
    if status and str(status).upper() == "NOT_FOUND":
        return True
    return "not found" in message.lower()


def _is_plan_limited(exc: BadResponse) -> bool:
    status, message = _parse_error(exc)
    if status and status.upper() in {"NOT_AUTHORIZED", "FORBIDDEN"}:
        return True
    lowered = message.lower()
    return "upgrade your plan" in lowered or "not authorized" in lowered


def _agg_to_dict(agg: Any) -> dict[str, Any]:
    return {
        "o": agg.open,
        "h": agg.high,
        "l": agg.low,
        "c": agg.close,
        "v": agg.volume,
        "t": agg.timestamp,
        "vw": getattr(agg, "vwap", None),
        "n": getattr(agg, "transactions", None),
    }


def _prev_close_to_dict(agg: Any) -> dict[str, Any]:
    return {
        "T": agg.ticker,
        "c": agg.close,
        "h": agg.high,
        "l": agg.low,
        "o": agg.open,
        "t": agg.timestamp,
        "v": agg.volume,
        "vw": getattr(agg, "vwap", None),
    }


def _premarket_to_dict(doc: Any) -> dict[str, Any]:
    if doc is None:
        return {}
    data = asdict(doc)
    return {
        "preMarketHigh": data.get("high"),
        "preMarketLow": data.get("low"),
        "preMarketOpen": data.get("open"),
        "preMarketClose": data.get("close"),
        "preMarket": data.get("pre_market"),
    }


def _quote_from_snapshot(snapshot: Any) -> dict[str, Any]:
    if not snapshot or not snapshot.last_quote:
        return {}
    bid = snapshot.last_quote.bid_price
    ask = snapshot.last_quote.ask_price
    mid = (bid + ask) / 2 if bid is not None and ask is not None else None
    spread_pct = None
    if mid and bid is not None and ask is not None and mid != 0:
        spread_pct = round(((ask - bid) / mid) * 100, 3)
    quality = "stable"
    if bid is None or ask is None:
        quality = "unknown"
    elif ask < bid:
        quality = "crossed"
    elif ask == bid:
        quality = "locked"
    return {
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_pct_of_mid": spread_pct,
        "nbbo_quality": quality,
    }


def _option_snapshot_to_dict(snapshot: Any) -> dict[str, Any]:
    details = snapshot.details
    quote = snapshot.last_quote
    greeks = snapshot.greeks
    day = snapshot.day
    bid = quote.bid if quote else None
    ask = quote.ask if quote else None
    mid = (bid + ask) / 2 if bid is not None and ask is not None else None
    spread_pct = None
    if mid and bid is not None and ask is not None and mid != 0:
        spread_pct = round(((ask - bid) / mid) * 100, 3)
    return {
        "contract": details.ticker if details else None,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_pct_of_mid": spread_pct,
        "oi": snapshot.open_interest,
        "volume": day.volume if day else None,
        "iv": snapshot.implied_volatility,
        "delta": greeks.delta if greeks else None,
        "theta": greeks.theta if greeks else None,
        "nbbo_quality": "stable" if bid is not None and ask is not None else "unknown",
    }


class MassiveClient:
    def __init__(self) -> None:
        if not settings.massive_api_key:
            raise RuntimeError("Massive API key required")
        # pagination disabled to avoid iterating massive payloads when we only need latest window
        self._client = RESTClient(
            api_key=settings.massive_api_key,
            pagination=False,
            num_pools=50,
            read_timeout=15.0,
            retries=5,
        )

    async def __aenter__(self) -> "MassiveClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - nothing to cleanup
        return None

    async def get_aggregates(self, ticker: str, timespan: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        def _fetch() -> list[dict[str, Any]]:
            aggs = self._client.get_aggs(ticker, 1, timespan, start, end) or []
            return [_agg_to_dict(agg) for agg in aggs]

        return await asyncio.to_thread(_fetch)

    async def get_previous_close(self, ticker: str) -> dict[str, Any]:
        def _fetch() -> dict[str, Any]:
            results = self._client.get_previous_close_agg(ticker) or []
            converted = [_prev_close_to_dict(r) for r in results]
            return {"results": converted, "ticker": ticker}

        return await asyncio.to_thread(_fetch)

    async def get_premarket_range(self, ticker: str, as_of: datetime) -> dict[str, Any]:
        def _fetch() -> dict[str, Any]:
            try:
                doc = self._client.get_daily_open_close_agg(ticker, as_of.date())
            except BadResponse as exc:
                if _is_not_found(exc) or _is_plan_limited(exc):
                    return {}
                raise
            return _premarket_to_dict(doc)

        return await asyncio.to_thread(_fetch)

    async def get_quote_snapshot(self, ticker: str) -> dict[str, Any]:
        def _fetch() -> dict[str, Any]:
            try:
                snapshot = self._client.get_snapshot_ticker("stocks", ticker)
            except BadResponse as exc:
                if _is_not_found(exc) or _is_plan_limited(exc):
                    return {}
                raise
            return _quote_from_snapshot(snapshot)

        return await asyncio.to_thread(_fetch)

    async def get_options_chain(self, ticker: str, as_of: datetime, limit: int = 100) -> list[dict[str, Any]]:
        def _fetch() -> list[dict[str, Any]]:
            snapshots: list[dict[str, Any]] = []
            try:
                for idx, snap in enumerate(self._client.list_snapshot_options_chain(ticker)):
                    if snap is None:
                        continue
                    option_dict = _option_snapshot_to_dict(snap)
                    if option_dict.get("contract"):
                        snapshots.append(option_dict)
                    if idx + 1 >= limit:
                        break
            except BadResponse as exc:
                if not (_is_not_found(exc) or _is_plan_limited(exc)):
                    raise
            return snapshots

        return await asyncio.to_thread(_fetch)
