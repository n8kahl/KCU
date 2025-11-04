from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import settings
from app.services.tile_engine import run_tile_simulator
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
    asyncio.create_task(run_tile_simulator(manager))


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
