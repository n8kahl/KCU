from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
async def send_alert(webhook_url: str, content: str) -> None:
    if not webhook_url:
        logger.info("discord-webhook-missing", extra={"event": "alert-skipped"})
        return
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(webhook_url, json={"content": content[:1900]})
        response.raise_for_status()
