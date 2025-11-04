from __future__ import annotations

import asyncio
from typing import Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        async with self._lock:
            recipients = list(self._connections)
        for connection in recipients:
            await connection.send_json(payload)

    async def heartbeat(self) -> None:
        while True:
            await asyncio.sleep(20)
            await self.broadcast({"type": "heartbeat"})
