from __future__ import annotations

import asyncio

from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import settings
from app.domain.types import ProbabilityBand, TileState
from app.ws.manager import ConnectionManager

configure_logging()
app = FastAPI(title="KCU LTP", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowlist,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
register_exception_handlers(app)

manager = ConnectionManager()


@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(manager.heartbeat())


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await manager.broadcast(
        {
            "type": "tile",
            "data": TileState(
                symbol="SPY",
                regime="Normal",
                probability_to_action=0.7,
                band=ProbabilityBand.from_score(75),
                confidence={"p50": 0.65, "p68": 0.1, "p95": 0.2},
                breakdown=[{"name": "Trend", "score": 0.8}],
                options={
                    "spread_pct": 5,
                    "ivr": 40,
                    "delta_target": 0.42,
                    "oi": 20000,
                    "volume": 10000,
                    "nbbo": "stable",
                    "liquidity_score": 85,
                },
                rationale={"positives": ["VWAP"], "risks": ["Event"]},
                admin={"mode": "Standard", "overrides": {}},
                timestamps={"updated": datetime.now(timezone.utc).isoformat()},
                eta_seconds=None,
                penalties={"chop": -5},
                bonuses={"king_queen": 8},
                history=[],
            ).model_dump(),
        }
    )
    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast({"echo": message})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
