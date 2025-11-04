from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
from typing import Iterable

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.domain.types import TileState

router = APIRouter()


def _mock_snapshots(limit: int = 5) -> Iterable[TileState]:
    base = datetime.now(timezone.utc)
    for idx in range(limit):
        yield TileState(
            symbol="SPY",
            regime="Normal",
            probability_to_action=0.75,
            band=TileState.default_band(),
            confidence={"p50": 0.7, "p68": 0.12, "p95": 0.2},
            breakdown=[{"name": "TrendStack", "score": 0.8}],
            options={"spread_pct": 4.5, "ivr": 30, "delta_target": 0.42, "oi": 50000, "volume": 20000, "nbbo": "stable", "liquidity_score": 90},
            rationale={"positives": ["Trend"], "risks": ["Event"]},
            admin={"mode": "Standard", "overrides": {}},
            timestamps={"updated": base.isoformat()},
            eta_seconds=None,
            penalties={"chop": -5},
            bonuses={"king_queen": 8},
            history=[],
        )


@router.get("/snapshots/query")
async def query_snapshots(
    ticker: str | None = None,
    regime: str | None = None,
    format: str = Query(default="json", pattern="^(json|csv)$"),
):
    rows = list(_mock_snapshots())
    if format == "json":
        return {"snapshots": [row.model_dump() for row in rows]}

    buffer = StringIO()
    buffer.write("symbol,regime,probability\n")
    for row in rows:
        buffer.write(f"{row.symbol},{row.regime},{row.probability_to_action}\n")
    return PlainTextResponse(buffer.getvalue(), media_type="text/csv")
