from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from app.domain.types import TileState
from app.services.state_store import state_store
from app.services.tile_engine import refresh_symbol
from app.services.watchlist import watchlist_service

router = APIRouter()


class TickerIn(BaseModel):
    ticker: str


@router.get("/tickers")
async def list_tickers() -> dict[str, list[str]]:
    return {"tickers": await watchlist_service.list()}


@router.post("/tickers")
async def add_ticker(payload: TickerIn = Body(...)) -> dict[str, list[str]]:
    tickers = await watchlist_service.add(payload.ticker)
    await refresh_symbol(payload.ticker.upper())
    return {"tickers": tickers}


@router.delete("/tickers/{symbol}")
async def remove_ticker(symbol: str) -> dict[str, list[str]]:
    tickers = await watchlist_service.remove(symbol)
    return {"tickers": tickers}


@router.get("/tickers/{symbol}/state")
async def get_symbol_state(symbol: str) -> TileState:
    symbol = symbol.upper()
    if symbol not in await watchlist_service.list():
        raise HTTPException(status_code=404, detail="Unknown symbol")

    cached = await state_store.get_state(symbol)
    if cached:
        return cached

    tile = await refresh_symbol(symbol)
    return tile
