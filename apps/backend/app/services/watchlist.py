from __future__ import annotations

import asyncio
import logging
from typing import List

from sqlalchemy import Select, delete, insert, select
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.settings import settings
from app.db.models_watchlist import WatchlistItem
from app.db.session import async_session, engine


class WatchlistService:
    def __init__(self) -> None:
        self._event = asyncio.Event()
        self._logger = logging.getLogger(__name__)
        self._memory = [ticker.upper() for ticker in settings.watchlist]
        self._db_warning_logged = False

    def _log_db_warning(self, key: str, error: str) -> None:
        if not self._db_warning_logged:
            self._logger.warning(key, extra={"error": error})
            self._db_warning_logged = True

    def _clear_db_warning(self) -> None:
        if self._db_warning_logged:
            self._db_warning_logged = False

    async def _ensure_table(self) -> None:
        if self._table_ready:
            return
        async with engine.begin() as conn:
            await conn.run_sync(WatchlistItem.__table__.create, checkfirst=True)
        self._table_ready = True

    def _table_missing(self, exc: Exception) -> bool:
        message = str(exc).lower()
        indicators = ["does not exist", "no such table", "undefined table"]
        return "watchlist" in message and any(token in message for token in indicators)

    async def seed_if_empty(self) -> None:
        ensured = False
        while True:
            try:
                async with async_session() as session:
                    existing = (
                        (await session.execute(select(WatchlistItem).limit(1))).scalars().all()
                    )
                    if existing:
                        self._clear_db_warning()
                        return
                    rows = [
                        {"ticker": ticker, "position": idx}
                        for idx, ticker in enumerate(settings.watchlist)
                    ]
                    if rows:
                        await session.execute(insert(WatchlistItem).values(rows))
                        await session.commit()
                        self._event.set()
                        self._clear_db_warning()
                return
            except (ProgrammingError, OperationalError) as exc:  # pragma: no cover - degraded env
                if self._table_missing(exc) and not ensured:
                    ensured = True
                    await self._ensure_table()
                    continue
                self._log_db_warning("watchlist-seed-failed", str(exc))
                return
            except Exception as exc:  # pragma: no cover
                self._log_db_warning("watchlist-seed-failed", str(exc))
                return

    async def list(self) -> List[str]:
        ensured = False
        while True:
            try:
                async with async_session() as session:
                    stmt: Select = select(WatchlistItem).order_by(
                        WatchlistItem.position.asc(), WatchlistItem.ticker.asc()
                    )
                    rows = (await session.execute(stmt)).scalars().all()
                symbols = [row.ticker.upper() for row in rows]
                if symbols:
                    self._memory = symbols
                self._table_ready = True
                self._clear_db_warning()
                return symbols or list(self._memory)
            except (ProgrammingError, OperationalError) as exc:  # pragma: no cover - degraded env
                if self._table_missing(exc) and not ensured:
                    ensured = True
                    await self._ensure_table()
                    continue
                self._log_db_warning("watchlist-list-failed", str(exc))
                return list(self._memory)
            except Exception as exc:  # pragma: no cover
                self._log_db_warning("watchlist-list-failed", str(exc))
                return list(self._memory)

    async def add(self, ticker: str) -> List[str]:
        ticker = ticker.upper()
        ensured = False
        while True:
            try:
                async with async_session() as session:
                    positions = (
                        (await session.execute(select(WatchlistItem.position))).scalars().all()
                    )
                    next_pos = (max(positions) + 1) if positions else 0
                    try:
                        await session.execute(
                            insert(WatchlistItem).values({"ticker": ticker, "position": next_pos})
                        )
                        await session.commit()
                    except Exception:
                        await session.rollback()
                self._event.set()
                self._table_ready = True
                self._clear_db_warning()
                return await self.list()
            except (ProgrammingError, OperationalError) as exc:  # pragma: no cover
                if self._table_missing(exc) and not ensured:
                    ensured = True
                    await self._ensure_table()
                    continue
                self._log_db_warning("watchlist-add-failed", str(exc))
                break
            except Exception as exc:  # pragma: no cover
                self._log_db_warning("watchlist-add-failed", str(exc))
                break
        if ticker not in self._memory:
            self._memory.append(ticker)
        self._event.set()
        return list(self._memory)

    async def remove(self, ticker: str) -> List[str]:
        ticker = ticker.upper()
        ensured = False
        while True:
            try:
                async with async_session() as session:
                    await session.execute(
                        delete(WatchlistItem).where(WatchlistItem.ticker == ticker)
                    )
                    await session.commit()
                self._event.set()
                self._table_ready = True
                self._clear_db_warning()
                return await self.list()
            except (ProgrammingError, OperationalError) as exc:  # pragma: no cover
                if self._table_missing(exc) and not ensured:
                    ensured = True
                    await self._ensure_table()
                    continue
                self._log_db_warning("watchlist-remove-failed", str(exc))
                break
            except Exception as exc:  # pragma: no cover
                self._log_db_warning("watchlist-remove-failed", str(exc))
                break
        self._memory = [t for t in self._memory if t != ticker]
        self._event.set()
        return list(self._memory)

    def event(self) -> asyncio.Event:
        return self._event


watchlist_service = WatchlistService()
