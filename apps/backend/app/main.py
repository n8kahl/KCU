from __future__ import annotations

import asyncio

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import api_router
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import settings
from app.db.session import engine
from app.services.realtime_engine import start_realtime
from app.services.state_store import state_store
from app.services.tile_engine import run_tile_pipeline
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
logger = logging.getLogger("uvicorn")


@app.on_event("startup")
async def startup_event() -> None:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
        logger.info("DB connection OK")
    except Exception:
        logger.exception("DB connection FAILED")
    asyncio.create_task(manager.heartbeat())
    asyncio.create_task(run_tile_pipeline(manager))
    asyncio.create_task(start_realtime(manager))


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    current = await state_store.all_states()
    for tile in current:
        await websocket.send_json({"type": "tile", "data": tile.model_dump()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
