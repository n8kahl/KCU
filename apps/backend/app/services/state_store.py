from __future__ import annotations

import asyncio
from typing import Dict

from app.domain.types import TileState


class StateStore:
    def __init__(self) -> None:
        self._states: Dict[str, TileState] = {}
        self._lock = asyncio.Lock()

    async def set_state(self, symbol: str, state: TileState) -> TileState:
        async with self._lock:
            self._states[symbol] = state
        return state

    async def get_state(self, symbol: str) -> TileState | None:
        async with self._lock:
            return self._states.get(symbol)

    async def all_states(self) -> list[TileState]:
        async with self._lock:
            return list(self._states.values())


state_store = StateStore()
