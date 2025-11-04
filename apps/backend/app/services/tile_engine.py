from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import random

from app.core.settings import settings
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

state_machine = StateMachine()


def _build_contributions() -> dict[str, float]:
    trend = trend_stack(random.uniform(-0.05, 0.08), random.random(), random.random(), [random.randint(0, 1) for _ in range(5)])
    levels = levels_cluster(random.uniform(-1, 1), random.random(), random.uniform(-1, 1))
    patience = patience_candle_quality(random.random(), random.uniform(0.5, 1.5), random.uniform(-1, 1))
    orb = orb_regime_score(random.random(), random.randint(120, 900), random.choice([True, False]))
    market = market_filters(random.random(), random.random(), random.random())
    options = options_health_base(random.uniform(3, 12), random.randint(5000, 40000), random.uniform(10, 90), random.choice(["stable", "flicker"]))
    return {
        "TrendStack": trend["score"],
        "Levels": levels["score"],
        "Patience": patience["score"],
        "ORB": orb["score"],
        "Market": market["score"],
        "Options": options["score"],
    }


def _penalties() -> dict[str, float]:
    return {
        "chop": random.uniform(-12, -3),
        "breadth": random.uniform(-8, 0),
    }


def _bonuses() -> dict[str, float]:
    values = {}
    if random.random() > 0.5:
        values["king_queen"] = random.uniform(5, 12)
    if random.random() > 0.6:
        values["orb_retest"] = random.uniform(3, 8)
    return values


def build_tile(symbol: str) -> TileState:
    contributions = _build_contributions()
    penalties = _penalties()
    bonuses = _bonuses()
    probability, band = aggregate_probability(contributions, penalties, bonuses)
    now = datetime.now(timezone.utc)
    confidence = confidence_interval(int(probability * 100), 120, random.choice(["Calm", "Normal", "Fast"]))
    options_snapshot = {
        "spread_pct": round(random.uniform(3, 10), 2),
        "ivr": int(random.uniform(20, 70)),
        "delta_target": round(random.uniform(0.35, 0.55), 2),
        "oi": random.randint(10000, 90000),
        "volume": random.randint(5000, 50000),
        "nbbo": random.choice(["stable", "locked", "crossed"]),
    }
    options_snapshot["liquidity_score"] = diagnostics(options_snapshot)["liquidity_score"]
    rationale = {
        "positives": ["Trend stack aligned", "Regime supportive"],
        "risks": ["Macro event" if probability < 0.6 else "Spread widening"],
    }
    eta = random.randint(30, 120) if band.label == "Loading" else None
    state = state_machine.derive_state(symbol, probability * 100)
    history = [
        {"ts": (now - timedelta(minutes=i)).isoformat(), "score": round(probability * 100 - i, 2)}
        for i in range(1, 4)
    ]
    return TileState(
        symbol=symbol,
        regime="Fast" if probability > 0.8 else "Normal",
        probability_to_action=probability,
        band=band,
        confidence=confidence,
        breakdown=[{"name": name, "score": round(score, 2)} for name, score in contributions.items()],
        options=options_snapshot,
        rationale=rationale,
        admin={"mode": "Standard", "overrides": {}},
        timestamps={"updated": now.isoformat()},
        eta_seconds=eta,
        penalties=penalties,
        bonuses=bonuses,
        history=history,
    )


async def run_tile_simulator(manager: ConnectionManager) -> None:
    await asyncio.sleep(1)
    while True:
        for symbol in settings.watchlist:
            tile = build_tile(symbol)
            await state_store.set_state(symbol, tile)
            await manager.broadcast({"type": "tile", "data": tile.model_dump()})
        await asyncio.sleep(5)
