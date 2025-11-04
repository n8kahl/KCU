from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.settings import settings
from app.domain.what_if import evaluate_what_if

router = APIRouter()


class WhatIfPayload(BaseModel):
    ticker: str = Field(..., min_length=1)
    deltas: dict[str, float | bool]


@router.post("/what-if")
async def run_what_if(payload: WhatIfPayload) -> dict[str, float | str | None]:
    ticker = payload.ticker.upper()
    if ticker not in settings.watchlist:
        raise HTTPException(status_code=404, detail="Unknown symbol")

    result = evaluate_what_if(ticker, payload.deltas)
    return {
        "symbol": ticker,
        "revisedProbToAction": result.probability,
        "revisedBand": result.band.label,
        "revisedETAsec": result.eta_seconds,
    }
