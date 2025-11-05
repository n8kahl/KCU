from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.adapters.massive import MassiveClient
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
from app.domain.options.buckets import ETF_INDEX, contract_metadata, option_bucket
from app.domain.options_health import diagnostics
from app.domain.scoring import aggregate_probability, confidence_interval
from app.domain.types import TileState
from app.services.baselines import baseline_service, percentile_rank, percentile_to_label
from app.services.state_machine import StateMachine
from app.services.state_store import state_store
from app.services.timing import get_timing_context
from app.services.tp_manager import tp_manager
from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)
REFRESH_SECONDS = 60
state_machine = StateMachine()


def _default_market_micro() -> dict[str, float]:
    return {"minuteThrust": 0.0, "microChop": 0.0, "divergenceZ": 0.0, "secVariance": 0.0}


def _structure_flags(closes: list[float]) -> list[int]:
    flags: list[int] = []
    for prev, curr in zip(closes[:-1], closes[1:]):
        flags.append(1 if curr >= prev else 0)
    return flags or [0]


def _safe_mean(values: list[float], default: float = 0.0) -> float:
    return mean(values) if values else default


def _atr(candles: list[dict[str, Any]], period: int = 5) -> float | None:
    if len(candles) < 2:
        return None
    closes = [c.get("c") for c in candles if c.get("c") is not None]
    if len(closes) < 2:
        return None
    trs: list[float] = []
    prev_close = closes[-period - 1] if len(closes) > period else closes[0]
    for candle in candles[-period:]:
        high = candle.get("h") or prev_close
        low = candle.get("l") or prev_close
        tr = max(high - low, abs(high - prev_close), abs(prev_close - low))
        trs.append(tr)
        prev_close = candle.get("c", prev_close)
    if not trs:
        return None
    return float(sum(trs) / len(trs))


async def _fetch_massive_payload(symbol: str) -> dict[str, Any]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=2)
    async with MassiveClient() as client:
        candles = await client.get_aggregates(symbol, "minute", start, end)
        prev_close = await client.get_previous_close(symbol)
        premarket_range = await client.get_premarket_range(symbol, end)
        quote = await client.get_quote_snapshot(symbol)
        options_chain = await client.get_options_chain(symbol, end)
    return {
        "candles": candles[-100:],
        "prev_close": prev_close,
        "premarket": premarket_range or {},
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
            "contracts": {"primary": None, "backups": []},
        }
    ordered = sorted(options_chain, key=lambda c: abs((c.get("delta") or 0) - 0.4))
    pick = ordered[0]
    backups = [doc.get("contract") for doc in ordered[1:3] if doc.get("contract")]
    primary = pick.get("contract")
    return {
        "spread_pct": pick.get("spread_pct_of_mid"),
        "ivr": pick.get("iv"),
        "delta_target": pick.get("delta"),
        "oi": pick.get("oi"),
        "volume": pick.get("volume"),
        "nbbo": pick.get("nbbo_quality", "stable"),
        "contracts": {"primary": primary, "backups": backups},
        "flicker_per_sec": None,
        "spread_percentile_rank": None,
        "flicker_percentile_rank": None,
        "ivr_percentile_rank": None,
        "vo_vol_percentile_rank": None,
        "liquidity_risk": None,
        "vo_vol": None,
        "dte_days": None,
        "bucket_key": None,
        "spread_percentile_label": "p--",
        "flicker_label": "p--",
    }


def _calc_vo_vol(candles: list[dict[str, Any]]) -> float | None:
    closes = [c.get("c") for c in candles if c.get("c")]
    if len(closes) < 10:
        return None
    returns = [(b - a) / a for a, b in zip(closes[:-1], closes[1:]) if a]
    if len(returns) < 5:
        return None
    return round(pstdev(returns), 6)


def _options_snapshot(symbol: str, payload: dict[str, Any]) -> dict[str, Any]:
    summary = _summarize_options(payload.get("options_chain", []))
    summary["liquidity_score"] = diagnostics(
        {
            "spread_pct": summary.get("spread_pct", 10) or 10,
            "oi": summary.get("oi", 10000) or 10000,
            "ivr": summary.get("ivr", 30) or 30,
            "nbbo": summary.get("nbbo", "stable"),
        }
    )["liquidity_score"]
    summary["vo_vol"] = _calc_vo_vol(payload.get("candles", []))
    metadata = contract_metadata(summary.get("contracts", {}).get("primary"))
    summary["dte_days"] = metadata.get("dte")
    summary["side"] = metadata.get("side")
    summary["bucket_key"] = option_bucket(symbol, summary.get("delta_target"), summary.get("dte_days"), summary.get("side"))
    return summary


async def _hydrate_options_metrics(symbol: str, options: dict[str, Any]) -> dict[str, Any]:
    if not options.get("bucket_key"):
        metadata = contract_metadata(options.get("contracts", {}).get("primary"))
        options["dte_days"] = metadata.get("dte")
        options["side"] = metadata.get("side")
        options["bucket_key"] = option_bucket(symbol, options.get("delta_target"), options.get("dte_days"), options.get("side"))
    bucket = options.get("bucket_key")
    spread_baseline = await baseline_service.get_percentiles("spread_pct", bucket) if bucket else None
    flicker_baseline = await baseline_service.get_percentiles("flicker_per_sec", bucket) if bucket else None
    ivr_baseline = await baseline_service.get_percentiles("iv_rank", bucket) if bucket else None
    vov_baseline = await baseline_service.get_percentiles("vo_vol", bucket) if bucket else None
    options["spread_percentile_rank"] = percentile_rank(options.get("spread_pct"), spread_baseline)
    options["flicker_percentile_rank"] = percentile_rank(options.get("flicker_per_sec"), flicker_baseline)
    options["ivr_percentile_rank"] = percentile_rank(options.get("ivr"), ivr_baseline)
    options["vo_vol_percentile_rank"] = percentile_rank(options.get("vo_vol"), vov_baseline)
    options["spread_percentile_label"] = percentile_to_label(options.get("spread_percentile_rank"))
    options["flicker_label"] = percentile_to_label(options.get("flicker_percentile_rank"))
    options["liquidity_risk"] = _liquidity_risk_score(options)
    return options


def _index_bucket(symbol: str) -> str | None:
    idx = ETF_INDEX.get(symbol)
    if not idx:
        return None
    return f"IDX:{idx}"


def _liquidity_risk_score(options: dict[str, Any]) -> float | None:
    spread_rank = options.get("spread_percentile_rank")
    flicker_rank = options.get("flicker_percentile_rank")
    ivr = options.get("ivr")
    oi = options.get("oi") or 0
    spread_pct = options.get("spread_pct")
    nbbo = (options.get("nbbo") or "unknown").lower()

    def _score_from_rank(rank: float | None) -> float:
        if rank is None:
            return 60.0
        rank = max(0.0, min(1.0, rank))
        return (1 - rank) * 100

    spread_component = _score_from_rank(spread_rank)
    flicker_component = _score_from_rank(flicker_rank)
    nbbo_component = {
        "stable": 100,
        "locked": 60,
        "crossed": 40,
    }.get(nbbo, 70)
    nbbo_flicker = 0.5 * nbbo_component + 0.5 * flicker_component
    oi_component = min(100.0, (oi / 5000) * 100)
    ivr_component = 100 - min(100, abs((ivr or 50) - 50) * 2)
    residual = max(0.0, 100 - (spread_pct or 0) * 8)
    score = 0.4 * spread_component + 0.2 * nbbo_flicker + 0.15 * oi_component + 0.15 * ivr_component + 0.1 * residual
    return round(min(max(score, 0.0), 100.0), 2)


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
    premarket = payload.get("premarket") or {}
    if not premarket:
        recent_window = closes[:5] if len(closes) >= 5 else closes
        pre_high = max(recent_window)
        pre_low = min(recent_window)
    else:
        pre_high = premarket.get("preMarketHigh") or last_price
        pre_low = premarket.get("preMarketLow") or last_price
    distance_to_level = (last_price - pre_high) / pre_high
    anchored_vwap_dist = (last_price - prior_close) / prior_close
    orb_window = closes[:15] if len(closes) >= 15 else closes
    orb_high = max(orb_window) if orb_window else last_price
    orb_low = min(orb_window) if orb_window else last_price
    orb_overlap = (orb_high - orb_low) / max(last_price, 1)
    levels = levels_cluster(distance_to_level, abs(orb_overlap), anchored_vwap_dist)
    level_stack = [
        {"label": "Premarket High", "price": pre_high},
        {"label": "Premarket Low", "price": pre_low},
        {"label": "Prior High", "price": prior.get("h")},
        {"label": "Prior Low", "price": prior.get("l")},
        {"label": "Prior Close", "price": prior_close},
        {"label": "ORB High", "price": orb_high},
        {"label": "ORB Low", "price": orb_low},
    ]

    last_candle = candles[-1] if candles else {"o": last_price, "c": last_price, "h": last_price, "l": last_price, "v": 0}
    body = abs(last_candle.get("c", last_price) - last_candle.get("o", last_price))
    range_ = (last_candle.get("h", last_price) - last_candle.get("l", last_price)) or 1
    body_pct = body / range_
    wick_ratio = (last_candle.get("h", last_price) - last_candle.get("c", last_price) + (last_candle.get("o", last_price) - last_candle.get("l", last_price))) or 1
    patience = patience_candle_quality(body_pct, wick_ratio, _normalize(last_candle.get("v", 0), 0, 1))

    adr = (max(closes) - min(closes)) / prior_close if prior_close else 0.01
    range_pct_adr = (orb_high - orb_low) / max(prior_close * adr, 1e-6)
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
    atr_value = _atr(candles)

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
        "series": {"closes": closes[-120:] if len(closes) >= 2 else closes},
        "levels": [lvl for lvl in level_stack if lvl.get("price")],
        "atr": atr_value,
        "ema": ema_fast,
        "last_price": last_price,
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


def _apply_percentile_penalties(options: dict[str, Any], penalties: dict[str, float]) -> None:
    spread_rank = options.get("spread_percentile_rank")
    flicker_rank = options.get("flicker_percentile_rank")
    liquidity_risk = options.get("liquidity_risk")
    if spread_rank is not None:
        if spread_rank >= 0.85:
            penalties["spread_percentile"] = -10
        elif spread_rank >= 0.75:
            penalties["spread_percentile"] = -6
    if flicker_rank is not None and flicker_rank >= 0.75:
        penalties["flicker"] = -5
    if liquidity_risk is not None and liquidity_risk >= 70:
        penalties["liquidity_risk"] = -7


def _calculate_bonuses(contributions: dict[str, float], payload: dict[str, Any]) -> dict[str, float]:
    bonuses: dict[str, float] = {}
    if contributions["TrendStack"] > 0.7 and contributions["Patience"] > 0.6:
        bonuses["king_queen"] = 8
    if payload.get("quote", {}).get("spread_pct_of_mid") and payload["quote"]["spread_pct_of_mid"] < 4:
        bonuses["liquidity"] = 4
    return bonuses


def _build_rationale(contributions: dict[str, float], penalties: dict[str, float]) -> dict[str, list[str]]:
    positives = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)[:2]
    negatives = sorted(penalties.items(), key=lambda kv: kv[1])[:2]
    return {
        "positives": [f"{name} strong" for name, _ in positives],
        "risks": [f"Penalty: {name}" for name, _ in negatives] or ["Monitoring latencies"],
    }


async def _adjust_confidence(symbol: str, confidence: dict[str, float], options: dict[str, Any], market_micro: dict[str, Any]) -> dict[str, float]:
    adjustment = 0.0
    flicker_rank = options.get("flicker_percentile_rank") or 0.0
    if flicker_rank >= 0.75:
        adjustment += 0.04
    vo_vol_rank = options.get("vo_vol_percentile_rank") or 0.0
    if vo_vol_rank >= 0.75:
        adjustment += 0.03
    if options.get("liquidity_risk", 0) >= 70:
        adjustment += 0.05
    idx_bucket = _index_bucket(symbol)
    if idx_bucket and market_micro:
        baseline = await baseline_service.get_percentiles("micro_chop", idx_bucket)
        if baseline and market_micro.get("microChop") is not None and market_micro["microChop"] >= baseline.p75:
            adjustment += 0.04
    adjustment = min(adjustment, 0.12)
    confidence["p68"] = round(min(confidence["p68"] + adjustment, 0.99), 3)
    confidence["p95"] = round(min(confidence["p95"] + adjustment * 1.5, 0.99), 3)
    return confidence


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
    timing = get_timing_context(now)
    tile = TileState(
        symbol=symbol,
        regime="Normal",
        probability_to_action=probability,
        band=band,
        confidence=confidence,
        breakdown=[{"name": k, "score": v} for k, v in contributions.items()],
        options={
            "spread_pct": 6,
            "ivr": 35,
            "delta_target": 0.42,
            "oi": 20000,
            "volume": 10000,
            "nbbo": "stable",
            "liquidity_score": 70,
            "contracts": {"primary": None, "backups": []},
            "flicker_per_sec": 1.2,
            "spread_percentile_rank": 0.6,
            "flicker_percentile_rank": 0.6,
            "ivr_percentile_rank": 0.4,
            "vo_vol_percentile_rank": 0.5,
            "vo_vol": 0.001,
            "dte_days": 5,
            "bucket_key": "SPX:CALL:Delta[0.30-0.40]:DTE[3-7]",
            "spread_percentile_label": "p60",
            "flicker_label": "p60",
            "liquidity_risk": 60,
        },
        rationale={"positives": ["Synthetic pipeline"], "risks": ["Waiting on live key"]},
        admin={
            "mode": "Standard",
            "overrides": {},
            "marketMicro": _default_market_micro(),
            "last_1m_closes": [],
            "timing": timing,
            "lastPrice": 0.0,
            "orb": {"range_pct": 0.3, "retest_success": False},
        },
        timestamps={"updated": now.isoformat()},
        eta_seconds=60,
        penalties=penalties,
        bonuses=bonuses,
        history=[],
    )
    meta = {
        "orb": {"range_pct": 0.3, "retest_success": False},
        "patience": {"body_pct": 0.5, "wick_ratio": 1.0},
        "series": {"closes": []},
    }
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
                market_micro=tile.admin.get("marketMicro") if tile.admin else None,
            )
            session.add(snapshot)
            await session.commit()
    except SQLAlchemyError as exc:
        logger.warning("snapshot-persist-failed", extra={"symbol": symbol, "error": str(exc)})


async def merge_realtime_into_tile(symbol: str, deltas: dict[str, Any]) -> TileState:
    tile = await state_store.get_state(symbol)
    if not tile:
        tile, _ = await build_tile(symbol)
        await state_store.set_state(symbol, tile)
    if deltas.get("options"):
        updated_options = dict(tile.options or {})
        updated_options.update(deltas["options"])
        updated_options = await _hydrate_options_metrics(symbol, updated_options)
        tile.options = updated_options
        penalties = dict(tile.penalties or {})
        _apply_percentile_penalties(updated_options, penalties)
        tile.penalties = penalties
    contributions = {item["name"]: item["score"] for item in tile.breakdown}
    market_micro = deltas.get("marketMicro") or {}
    alpha = 0.55
    micro_signals: list[float] = []
    if "minuteThrust" in market_micro:
        micro_signals.append(max(0.0, float(market_micro["minuteThrust"])))
    if "microChop" in market_micro:
        micro_signals.append(max(0.0, 1.0 - float(market_micro["microChop"])))
    if "divergenceZ" in market_micro:
        micro_signals.append(max(0.0, 1.0 - min(1.0, abs(float(market_micro["divergenceZ"])) / 1.5)))
    if micro_signals:
        micro_sum = 0.0
        for idx, value in enumerate(sorted(micro_signals, reverse=True)):
            micro_sum += value / (1 + alpha * idx)
        target = micro_sum / len(micro_signals)
        contributions["Market"] = max(0.0, min(1.0, 0.6 * contributions.get("Market", 0.5) + 0.4 * target))

    penalties = dict(tile.penalties or {})
    if market_micro.get("microChop", 0) and market_micro["microChop"] >= 0.6:
        penalties["chop"] = -8
    if abs(float(market_micro.get("divergenceZ", 0) or 0)) >= 1.5:
        penalties["divergence"] = -6

    bonuses = dict(tile.bonuses or {})
    minute_ok = market_micro.get("minuteThrust", 0) > 0
    div_ok = abs(float(market_micro.get("divergenceZ", 0) or 0)) <= 0.7
    if not (minute_ok and div_ok):
        if "king_queen" in bonuses:
            bonuses["king_queen"] = max(0, int(bonuses["king_queen"] * 0.6))
        if "orb_retest" in bonuses:
            bonuses["orb_retest"] = max(0, int(bonuses["orb_retest"] * 0.6))

    probability, band = aggregate_probability(contributions, penalties, bonuses)
    confidence = confidence_interval(int(probability * 100), 150, tile.regime)
    confidence = await _adjust_confidence(symbol, confidence, tile.options or {}, {**tile.admin.get("marketMicro", {}), **market_micro})

    tile.breakdown = [{"name": name, "score": round(score, 3)} for name, score in contributions.items()]
    tile.penalties = penalties
    tile.bonuses = bonuses
    tile.probability_to_action = probability
    tile.band = band
    tile.confidence = confidence
    market_admin = tile.admin.get("marketMicro", _default_market_micro()) if tile.admin else _default_market_micro()
    merged_market = {**market_admin, **market_micro}
    admin = dict(tile.admin or {})
    admin["marketMicro"] = merged_market
    if "timing" not in admin:
        admin["timing"] = get_timing_context(datetime.now(timezone.utc))
    tile.admin = admin
    plan = await tp_manager.on_tick(
        symbol,
        admin.get("lastPrice"),
        tile.probability_to_action,
        (tile.options or {}).get("liquidity_risk") if tile.options else None,
        admin["marketMicro"],
        admin["timing"],
    )
    if plan:
        admin["managing"] = plan
        options = dict(tile.options or {})
        options["tp_plan"] = plan
        tile.options = options
    tile.timestamps["updated"] = datetime.now(timezone.utc).isoformat()
    await state_store.set_state(symbol, tile)
    return tile


async def build_tile(symbol: str) -> tuple[TileState, dict[str, Any]]:
    if not settings.massive_api_key:
        return _synthetic_tile(symbol)
    try:
        payload = await _fetch_massive_payload(symbol)
        contributions, meta = _compute_contributions(symbol, payload)
        penalties = _calculate_penalties(payload, contributions)
        bonuses = _calculate_bonuses(contributions, payload)
        probability, band = aggregate_probability(contributions, penalties, bonuses)
        confidence = confidence_interval(int(probability * 100), 150, "Normal")
        history_tile = await state_store.get_state(symbol)
        history = history_tile.history[-2:] if history_tile else []
        history.append({"ts": datetime.now(timezone.utc).isoformat(), "score": probability * 100})
        options_snapshot = _options_snapshot(symbol, payload)
        options_snapshot = await _hydrate_options_metrics(symbol, options_snapshot)
        _apply_percentile_penalties(options_snapshot, penalties)
        prev_micro = history_tile.admin.get("marketMicro") if history_tile and history_tile.admin else _default_market_micro()
        timing = get_timing_context(datetime.now(timezone.utc))
        last_price = meta.get("last_price")
        admin = {
            "mode": "Standard",
            "overrides": {},
            "marketMicro": prev_micro,
            "last_1m_closes": meta.get("series", {}).get("closes", []),
            "timing": timing,
            "lastPrice": last_price,
            "orb": meta.get("orb"),
        }
        await tp_manager.update_context(
            symbol,
            {
                "levels": meta.get("levels", []),
                "atr": meta.get("atr"),
                "ema": meta.get("ema"),
                "regime": "Fast" if probability > 0.8 else "Normal",
                "timing": timing,
                "last_price": last_price,
            },
        )
        confidence = await _adjust_confidence(symbol, confidence, options_snapshot, admin["marketMicro"])
        plan = await tp_manager.on_tick(
            symbol,
            last_price,
            probability,
            options_snapshot.get("liquidity_risk"),
            admin["marketMicro"],
            timing,
        )
        if plan:
            admin["managing"] = plan
            options_snapshot["tp_plan"] = plan
        tile = TileState(
            symbol=symbol,
            regime="Fast" if probability > 0.8 else "Normal",
            probability_to_action=probability,
            band=band,
            confidence=confidence,
            breakdown=[{"name": name, "score": round(score, 3)} for name, score in contributions.items()],
            options=options_snapshot,
            rationale=_build_rationale(contributions, penalties),
            admin=admin,
            timestamps={"updated": datetime.now(timezone.utc).isoformat()},
            eta_seconds=45 if band.label == "Loading" else None,
            penalties=penalties,
            bonuses=bonuses,
            history=history,
        )
        return tile, meta
    except Exception as exc:  # pragma: no cover - network failures fallback
        logger.warning("tile-build-fallback symbol=%s error=%s", symbol, exc, exc_info=True)
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
