from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def warm_candles(ticker: str) -> None:
    logger.info("warm-candles", extra={"ticker": ticker, "ts": datetime.now(timezone.utc).isoformat()})
    await asyncio.sleep(0.1)


async def poll_quotes(ticker: str) -> None:
    logger.debug("poll-quotes", extra={"ticker": ticker})
    await asyncio.sleep(0.1)
