from __future__ import annotations

import asyncio
from typing import Any, Dict


class QuoteCache:
    def __init__(self) -> None:
        self._quotes: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def set_quote(self, symbol: str, payload: dict) -> None:
        async with self._lock:
            self._quotes[symbol.upper()] = payload

    async def get_quote(self, symbol: str) -> dict | None:
        async with self._lock:
            return self._quotes.get(symbol.upper())


quote_cache = QuoteCache()

__all__ = ["quote_cache"]
