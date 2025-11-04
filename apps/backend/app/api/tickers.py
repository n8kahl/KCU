from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.settings import settings
from app.domain.types import TileState
from app.services.state_store import state_store
from app.services.tile_engine import build_tile

router = APIRouter()


@router.get("/tickers")
async def list_tickers() -> dict[str, list[str]]:
    return {"tickers": settings.watchlist}


@router.get("/tickers/{symbol}/state")
async def get_symbol_state(symbol: str) -> TileState:
    if symbol.upper() not in settings.watchlist:
        raise HTTPException(status_code=404, detail="Unknown symbol")

    cached = await state_store.get_state(symbol.upper())
    if cached:
        return cached

    tile = build_tile(symbol.upper())
    await state_store.set_state(symbol.upper(), tile)
    return tile
