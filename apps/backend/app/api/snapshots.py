from __future__ import annotations

import logging
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.models import Snapshot
from app.db.session import get_session_or_none
from app.domain.types import TileState
from app.services.state_store import state_store
from app.services.tile_engine import build_tile

logger = logging.getLogger(__name__)
router = APIRouter()


def _snapshot_to_dict(record: Snapshot) -> dict[str, Any]:
    return {
        "id": str(record.id),
        "ticker": record.ticker,
        "ts": record.ts.isoformat() if record.ts else None,
        "regime": record.regime,
        "score": float(record.score),
        "prob": record.prob,
        "bands": record.bands,
        "breakdown": record.breakdown,
        "options": record.options,
        "orb": record.orb,
        "patience": record.patience,
        "penalties": record.penalties,
        "bonuses": record.bonuses,
        "state": record.state,
        "rationale": record.rationale,
    }


async def _fallback_snapshots(ticker: str | None) -> list[dict[str, Any]]:
    cached = await state_store.all_states()
    if cached:
        return [tile.model_dump() for tile in cached if not ticker or tile.symbol == ticker.upper()]
    symbol = ticker.upper() if ticker else (settings.watchlist[0] if settings.watchlist else "SPY")
    tile, _ = await build_tile(symbol)
    return [tile.model_dump()]


@router.get("/snapshots/query")
async def query_snapshots(
    ticker: str | None = None,
    regime: str | None = None,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    session: AsyncSession | None = Depends(get_session_or_none),
):
    results: list[dict[str, Any]] = []
    if session is not None:
        try:
            stmt: Select[Snapshot] = select(Snapshot).order_by(Snapshot.ts.desc()).limit(200)
            if ticker:
                stmt = stmt.where(Snapshot.ticker == ticker.upper())
            if regime:
                stmt = stmt.where(Snapshot.regime == regime.title())
            db_rows = (await session.execute(stmt)).scalars().all()
            results = [_snapshot_to_dict(row) for row in db_rows]
        except Exception as exc:  # pragma: no cover - optional DB path
            logger.warning("snapshot-query-failed", extra={"error": str(exc)})
            results = []

    if not results:
        results = await _fallback_snapshots(ticker)

    if format == "json":
        return {"snapshots": results}

    buffer = StringIO()
    buffer.write("symbol,regime,probability\n")
    for row in results:
        prob = row.get("prob", {}).get("probability") or row.get("probability_to_action", "")
        buffer.write(f"{row.get('ticker','')},{row.get('regime','')},{prob}\n")
    return PlainTextResponse(buffer.getvalue(), media_type="text/csv")
