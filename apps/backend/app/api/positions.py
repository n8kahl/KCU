from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.tp_manager import tp_manager
from app.services.state_store import state_store

router = APIRouter(prefix="/positions")


class PositionStartRequest(BaseModel):
    symbol: str
    direction: str = Field(default="long", pattern="^(?i)(long|short)$")
    entry: float | None = None


class PositionStopRequest(BaseModel):
    symbol: str


@router.post("/start")
async def start_position(payload: PositionStartRequest):
    symbol = payload.symbol.upper()
    tile = await state_store.get_state(symbol)
    if not tile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not tracked")
    entry_price = payload.entry or tile.admin.get("lastPrice")
    if entry_price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entry price required")
    market_micro = tile.admin.get("marketMicro") or {}
    plan = await tp_manager.start(
        symbol,
        entry=entry_price,
        direction=payload.direction.lower(),
        regime=tile.regime,
        liquidity_risk=(tile.options or {}).get("liquidity_risk"),
        minute_thrust=market_micro.get("minuteThrust"),
        divergence=market_micro.get("divergenceZ"),
        timing=tile.admin.get("timing"),
    )
    return {"status": "started", "plan": plan}


@router.post("/stop")
async def stop_position(payload: PositionStopRequest):
    symbol = payload.symbol.upper()
    await tp_manager.stop(symbol)
    return {"status": "stopped", "symbol": symbol}
