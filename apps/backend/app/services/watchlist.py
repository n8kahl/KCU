from __future__ import annotations

import asyncio
import logging
from typing import List

from sqlalchemy import Select, delete, insert, select

from app.core.settings import settings
from app.db.models_watchlist import WatchlistItem
from app.db.session import async_session


class WatchlistService:
    def __init__(self) -> None:
        self._event = asyncio.Event()
        self._logger = logging.getLogger(__name__)
        self._memory = [ticker.upper() for ticker in settings.watchlist]

    async def seed_if_empty(self) -> None:
        try:
            async with async_session() as session:
                existing = (await session.execute(select(WatchlistItem).limit(1))).scalars().all()
                if existing:
                    return
                rows = [
                    {"ticker": ticker, "position": idx}
                    for idx, ticker in enumerate(settings.watchlist)
                ]
                if rows:
                    await session.execute(insert(WatchlistItem).values(rows))
                    await session.commit()
                    self._event.set()
        except Exception as exc:  # pragma: no cover - degraded env (no DB)
            self._logger.warning("watchlist-seed-failed", extra={"error": str(exc)})

    async def list(self) -> List[str]:
        try:
            async with async_session() as session:
                stmt: Select = select(WatchlistItem).order_by(
                    WatchlistItem.position.asc(), WatchlistItem.ticker.asc()
                )
                rows = (await session.execute(stmt)).scalars().all()
            symbols = [row.ticker.upper() for row in rows]
            if symbols:
                self._memory = symbols
            return symbols or list(self._memory)
        except Exception as exc:  # pragma: no cover - degraded env
            self._logger.warning("watchlist-list-failed", extra={"error": str(exc)})
            return list(self._memory)

    async def add(self, ticker: str) -> List[str]:
        ticker = ticker.upper()
        try:
            async with async_session() as session:
                positions = (await session.execute(select(WatchlistItem.position))).scalars().all()
                next_pos = (max(positions) + 1) if positions else 0
                try:
                    await session.execute(
                        insert(WatchlistItem).values({"ticker": ticker, "position": next_pos})
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
            self._event.set()
            return await self.list()
        except Exception as exc:  # pragma: no cover - degraded env
            self._logger.warning("watchlist-add-failed", extra={"error": str(exc)})
            if ticker not in self._memory:
                self._memory.append(ticker)
            self._event.set()
            return list(self._memory)

    async def remove(self, ticker: str) -> List[str]:
        ticker = ticker.upper()
        try:
            async with async_session() as session:
                await session.execute(delete(WatchlistItem).where(WatchlistItem.ticker == ticker))
                await session.commit()
            self._event.set()
            return await self.list()
        except Exception as exc:  # pragma: no cover - degraded env
            self._logger.warning("watchlist-remove-failed", extra={"error": str(exc)})
            self._memory = [t for t in self._memory if t != ticker]
            self._event.set()
            return list(self._memory)

    def event(self) -> asyncio.Event:
        return self._event


watchlist_service = WatchlistService()
