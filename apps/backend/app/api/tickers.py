from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import random
from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.settings import settings
from app.domain.types import ProbabilityBand, TileState
from app.services.state_machine import StateMachine

router = APIRouter()
state_machine = StateMachine()


@router.get("/tickers")
async def list_tickers() -> dict[str, list[str]]:
    return {"tickers": settings.watchlist}


@router.get("/tickers/{symbol}/state")
async def get_symbol_state(symbol: str) -> TileState:
    if symbol.upper() not in settings.watchlist:
        raise HTTPException(status_code=404, detail="Unknown symbol")

    now = datetime.now(timezone.utc)
    score = 60 + random() * 35
    state = state_machine.derive_state(symbol.upper(), score)
    return TileState(
        symbol=symbol.upper(),
        regime="Normal",
        probability_to_action=round(score / 100, 2),
        band=ProbabilityBand.from_score(score),
        confidence={"p50": 0.62, "p68": 0.1, "p95": 0.18},
        breakdown=[{"name": "TrendStack", "score": 0.8}, {"name": "Levels", "score": 0.6}],
        options={
            "spread_pct": 5.5,
            "ivr": 42,
            "delta_target": 0.4,
            "oi": 25000,
            "volume": 12000,
            "nbbo": "stable",
            "liquidity_score": 82,
        },
        rationale={
            "positives": ["VWAP + EMA alignment", "Breath confirm"],
            "risks": ["Event nearby"],
        },
        admin={"mode": "Standard", "overrides": {}},
        timestamps={"updated": now.isoformat()},
        eta_seconds=45 if state.label == "Loading" else None,
        penalties={"chop": -7},
        bonuses={"king_queen": 8},
        history=[
            {"ts": (now - timedelta(minutes=i)).isoformat(), "score": score - i}
            for i in range(1, 4)
        ],
    )
