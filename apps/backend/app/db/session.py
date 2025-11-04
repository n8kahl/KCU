from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import settings

logger = logging.getLogger(__name__)
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_session_or_none() -> AsyncSession | None:
    try:
        async with async_session() as session:
            yield session
    except Exception as exc:  # pragma: no cover - optional dependency path
        logger.warning("db-session-unavailable", extra={"error": str(exc)})
        yield None
