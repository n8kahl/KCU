from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.adapters.polygon import PolygonClient
from app.core.settings import settings
from app.db.models import Snapshot
from app.db.session import async_session
from app.domain.features import (
    levels_cluster,
    market_filters,
    options_health_base,
    orb_regime_score,
    patience_candle_quality,
    trend_stack,
)
from app.domain.options_health import diagnostics
from app.domain.scoring import aggregate_probability, confidence_interval
from app.domain.types import TileState
from app.services.state_machine import StateMachine
from app.services.state_store import state_store
from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)
REFRESH_SECONDS = 15
state_machine = StateMachine()


def _structure_flags(closes: list[float]) -> list[int]:
    flags: list[int] = []
    for prev, curr in zip(closes[:-1], closes[1:]):
        flags.append(1 if curr >= prev else 0)
    return flags or [0]


def _safe_mean(values: list[float], default: float = 0.0) -> float:
    return mean(values) if values else default


async def _fetch_polygon_payload(symbol: str) -> dict[str, Any]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=2)
    async with PolygonClient() as client:
        candles = await client.get_aggregates(symbol, "minute", start, end)
        prev_close = await client.get_previous_close(symbol)
        premarket_range = await client.get_premarket_range(symbol, end)
        quote = await client.get_quote_snapshot(symbol)
        options_chain = await client.get_options_chain(symbol, end)
    return {
        "candles": candles[-100:],
        "prev_close": prev_close,
        "premarket": premarket_range,
        "quote": quote,
        "options_chain": options_chain,
    }


def _summarize_options(options_chain: list[dict[str, Any]]) -> dict[str, Any]:
    if not options_chain:
        return {
            "spread_pct": None,
            "ivr": None,
            "delta_target": None,
            "oi": None,
            "volume": None,
            "nbbo": "unknown",
        }
    ordered = sorted(options_chain, key=lambda c: abs((c.get("delta") or 0) - 0.4))
    pick = ordered[0]
    return {
        "spread_pct": pick.get("spread_pct_of_mid"),
        "ivr": pick.get("iv"),
        "delta_target": pick.get("delta"),
        "oi": pick.get("oi"),
        "volume": pick.get("volume"),
        "nbbo": pick.get("nbbo_quality", "stable"),
    }


def _normalize(value: float, floor: float, ceiling: float) -> float:
    span = ceiling - floor
    if span == 0:
        return 0.5
    return max(0.0, min(1.0, (value - floor) / span))


def _compute_contributions(symbol: str, payload: dict[str, Any]) -> tuple[dict[str, float], dict[str, Any]]:
    candles = payload.get("candles", [])
    closes = [c.get("c") for c in candles if c.get("c")]
    if not closes:
        closes = [1.0, 1.0]
    ema_fast = _safe_mean(closes[-8:])
    ema_slow = _safe_mean(closes[-21:])
    vwap_proxy = (closes[-1] - closes[0]) / closes[0]
    structure = _structure_flags(closes[-6:])
    trend = trend_stack(vwap_proxy, ema_fast, ema_slow or ema_fast, structure)

    last_price = closes[-1]
    prior = payload.get("prev_close", {}).get("results", [{}])[0]
    prior_close = prior.get("c") or last_price
    premarket = payload.get("premarket", {})
    pre_high = premarket.get("preMarketHigh") or last_price
    distance_to_level = (last_price - pre_high) / pre_high
    anchored_vwap_dist = (last_price - prior_close) / prior_close
    orb_high = max(closes[:3]) if len(closes) >= 3 else last_price
    orb_low = min(closes[:3]) if len(closes) >= 3 else last_price
    orb_overlap = (orb_high - orb_low) / max(last_price, 1)
    levels = levels_cluster(distance_to_level, abs(orb_overlap), anchored_vwap_dist)

    last_candle = candles[-1] if candles else {"o": last_price, "c": last_price, "h": last_price, "l": last_price, "v": 0}
    body = abs(last_candle.get("c", last_price) - last_candle.get("o", last_price))
    range_ = (last_candle.get("h", last_price) - last_candle.get("l", last_price)) or 1
    body_pct = body / range_
    wick_ratio = (last_candle.get("h", last_price) - last_candle.get("c", last_price) + (last_candle.get("o", last_price) - last_candle.get("l", last_price))) or 1
    patience = patience_candle_quality(body_pct, wick_ratio, _normalize(last_candle.get("v", 0), 0, 1))

    adr = (max(closes) - min(closes)) / prior_close if prior_close else 0.01
    range_pct_adr = (orb_high - orb_low) / (prior_close * adr or 1)
    acceptance_time = len(candles)
    retest_success = last_price > orb_high
    orb = orb_regime_score(range_pct_adr, acceptance_time * 60, retest_success)

    spread_proxy = payload.get("quote", {}).get("spread_pct_of_mid") or 5
    nbbo_quality = payload.get("quote", {}).get("nbbo_quality", "stable")
    oi_depth = sum((c.get("oi") or 0) for c in payload.get("options_chain", [])[:5])
    iv_rank = _normalize(payload.get("quote", {}).get("iv" , 30) or 30, 0, 100) * 100
    options = options_health_base(spread_proxy, oi_depth or 10000, iv_rank, nbbo_quality)

    breadth = _normalize(last_price - prior_close, -2, 2)
    vix_proxy = _normalize(spread_proxy, 0, 20)
    spy_alignment = 0.7 if symbol != "SPY" else 0.9
    market = market_filters(breadth, vix_proxy, spy_alignment)

    contributions = {
        "TrendStack": trend["score"],
        "Levels": levels["score"],
        "Patience": patience["score"],
        "ORB": orb["score"],
        "Market": market["score"],
        "Options": options["score"],
    }
    meta = {
        "orb": {"range_pct": range_pct_adr, "retest_success": retest_success},
        "patience": {"body_pct": round(body_pct, 4), "wick_ratio": round(wick_ratio, 4)},
    }
    return contributions, meta


def _calculate_penalties(payload: dict[str, Any], contributions: dict[str, float]) -> dict[str, float]:
    penalties: dict[str, float] = {}
    spread = payload.get("quote", {}).get("spread_pct_of_mid") or 0
    if spread > 8:
        penalties["spread"] = -min(spread, 15)
    if payload.get("quote", {}).get("nbbo_quality") in {"locked", "crossed"}:
        penalties["nbbo"] = -8
    if contributions["Market"] < 0.4:
        penalties["breadth"] = -6
    return penalties


def _calculate_bonuses(contributions: dict[str, float], payload: dict[str, Any]) -> dict[str, float]:
    bonuses: dict[str, float] = {}
    if contributions["TrendStack"] > 0.7 and contributions["Patience"] > 0.6:
        bonuses["king_queen"] = 8
    if payload.get("quote", {}).get("spread_pct_of_mid") and payload["quote"]["spread_pct_of_mid"] < 4:
        bonuses["liquidity"] = 4
    return bonuses


def _options_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    summary = _summarize_options(payload.get("options_chain", []))
    summary["liquidity_score"] = diagnostics({
        "spread_pct": summary.get("spread_pct", 10) or 10,
        "oi": summary.get("oi", 10000) or 10000,
        "ivr": summary.get("ivr", 30) or 30,
        "nbbo": summary.get("nbbo", "stable"),
    })["liquidity_score"]
    return summary


def _build_rationale(contributions: dict[str, float], penalties: dict[str, float]) -> dict[str, list[str]]:
    positives = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)[:2]
    negatives = sorted(penalties.items(), key=lambda kv: kv[1])[:2]
    return {
        "positives": [f"{name} strong" for name, _ in positives],
        "risks": [f"Penalty: {name}" for name, _ in negatives] or ["Monitoring latencies"],
    }


def _synthetic_tile(symbol: str) -> tuple[TileState, dict[str, Any]]:
    now = datetime.now(timezone.utc)
    contributions = {
        "TrendStack": 0.6,
        "Levels": 0.55,
        "Patience": 0.58,
        "ORB": 0.5,
        "Market": 0.6,
        "Options": 0.45,
    }
    penalties = {"spread": -5}
    bonuses = {"king_queen": 6}
    probability, band = aggregate_probability(contributions, penalties, bonuses)
    confidence = confidence_interval(int(probability * 100), 100, "Normal")
    tile = TileState(
        symbol=symbol,
        regime="Normal",
        probability_to_action=probability,
        band=band,
        confidence=confidence,
        breakdown=[{"name": k, "score": v} for k, v in contributions.items()],
        options={"spread_pct": 6, "ivr": 35, "delta_target": 0.42, "oi": 20000, "volume": 10000, "nbbo": "stable", "liquidity_score": 70},
        rationale={"positives": ["Synthetic pipeline"], "risks": ["Waiting on live key"]},
        admin={"mode": "Standard", "overrides": {}},
        timestamps={"updated": now.isoformat()},
        eta_seconds=60,
        penalties=penalties,
        bonuses=bonuses,
        history=[],
    )
    meta = {"orb": {"range_pct": 0.3, "retest_success": False}, "patience": {"body_pct": 0.5, "wick_ratio": 1.0}}
    return tile, meta


async def _persist_snapshot(symbol: str, tile: TileState, meta: dict[str, Any]) -> None:
    try:
        async with async_session() as session:
            snapshot = Snapshot(
                ts=datetime.now(timezone.utc),
                ticker=symbol,
                regime=tile.regime,
                score=tile.probability_to_action * 100,
                prob={"probability": tile.probability_to_action},
                bands=tile.band.model_dump(),
                breakdown=tile.breakdown,
                options=tile.options,
                orb=meta.get("orb", {}),
                patience=meta.get("patience", {}),
                penalties=tile.penalties,
                bonuses=tile.bonuses,
                state=tile.band.label,
                rationale=tile.rationale,
            )
            session.add(snapshot)
            await session.commit()
    except SQLAlchemyError as exc:
        logger.warning("snapshot-persist-failed", extra={"symbol": symbol, "error": str(exc)})


async def build_tile(symbol: str) -> tuple[TileState, dict[str, Any]]:
    if not settings.polygon_api_key:
        return _synthetic_tile(symbol)
    try:
        payload = await _fetch_polygon_payload(symbol)
        contributions, meta = _compute_contributions(symbol, payload)
        penalties = _calculate_penalties(payload, contributions)
        bonuses = _calculate_bonuses(contributions, payload)
        probability, band = aggregate_probability(contributions, penalties, bonuses)
        confidence = confidence_interval(int(probability * 100), 150, "Normal")
        history_tile = await state_store.get_state(symbol)
        history = history_tile.history[-2:] if history_tile else []
        history.append({"ts": datetime.now(timezone.utc).isoformat(), "score": probability * 100})
        tile = TileState(
            symbol=symbol,
            regime="Fast" if probability > 0.8 else "Normal",
            probability_to_action=probability,
            band=band,
            confidence=confidence,
            breakdown=[{"name": name, "score": round(score, 3)} for name, score in contributions.items()],
            options=_options_snapshot(payload),
            rationale=_build_rationale(contributions, penalties),
            admin={"mode": "Standard", "overrides": {}},
            timestamps={"updated": datetime.now(timezone.utc).isoformat()},
            eta_seconds=45 if band.label == "Loading" else None,
            penalties=penalties,
            bonuses=bonuses,
            history=history,
        )
        return tile, meta
    except Exception as exc:  # pragma: no cover - network failures fallback
        logger.warning("tile-build-fallback", extra={"symbol": symbol, "error": str(exc)})
        return _synthetic_tile(symbol)


async def refresh_symbol(symbol: str, manager: ConnectionManager | None = None) -> TileState:
    tile, meta = await build_tile(symbol)
    await state_store.set_state(symbol, tile)
    await _persist_snapshot(symbol, tile, meta)
    if manager:
        await manager.broadcast({"type": "tile", "data": tile.model_dump()})
    return tile


async def run_tile_pipeline(manager: ConnectionManager | None = None) -> None:
    if not settings.watchlist:
        return
    # small delay to allow startup wiring
    await asyncio.sleep(2)
    while True:
        for symbol in settings.watchlist:
            await refresh_symbol(symbol, manager)
        await asyncio.sleep(REFRESH_SECONDS)
