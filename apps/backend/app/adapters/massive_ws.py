from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import suppress
from typing import Awaitable, Callable

import websockets

logger = logging.getLogger(__name__)


def _nbbo_state(bp: float | None, ap: float | None) -> str:
    if bp is None or ap is None:
        return "unknown"
    if ap < bp:
        return "crossed"
    if ap == bp:
        return "locked"
    return "stable"


def _normalize_ts(value: int | float | str | None) -> int | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            # Massive sends ms since epoch
            return int(value)
        return int(float(value))
    except (TypeError, ValueError):
        return None


async def _subscription_sender(ws, queue: asyncio.Queue[str]) -> None:
    while True:
        params = await queue.get()
        payload = json.dumps({"action": "subscribe", "params": params})
        await ws.send(payload)


async def run_massive_ws(
    on_event: Callable[[dict], Awaitable[None]],
    subscription_queue: asyncio.Queue[str],
    snapshot_subscriptions: Callable[[], list[str]],
) -> None:
    """Connect to Massive WS, dispatch normalized events, and handle reconnects."""

    api_key = os.getenv("MASSIVE_API_KEY")
    if not api_key:
        raise RuntimeError("MASSIVE_API_KEY required for Massive WS streaming")

    url = os.getenv("MASSIVE_WS_URL", "wss://api.massive.com/v1/stream")
    backoff = 1

    while True:
        sender_task: asyncio.Task | None = None
        try:
            async with websockets.connect(url, extra_headers={"Authorization": f"Bearer {api_key}"}, ping_interval=None) as ws:
                logger.info("massive-ws-connected", extra={"url": url})
                # Re-hydrate subscriptions on every connect
                for params in snapshot_subscriptions():
                    await ws.send(json.dumps({"action": "subscribe", "params": params}))
                sender_task = asyncio.create_task(_subscription_sender(ws, subscription_queue))
                backoff = 1
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning("massive-ws-bad-json", extra={"raw": raw})
                        continue
                    event = _normalize_event(msg)
                    if event:
                        await on_event(event)
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("massive-ws-reconnect", extra={"error": str(exc), "backoff": backoff})
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 10)
        finally:
            if sender_task:
                sender_task.cancel()
                with suppress(asyncio.CancelledError):
                    await sender_task


def _normalize_event(msg: dict) -> dict | None:
    ev = msg.get("ev")
    if ev == "AM" and str(msg.get("sym", "")).startswith("I:"):
        sym = str(msg["sym"]).removeprefix("I:")
        return {
            "kind": "index_1m",
            "symbol": sym,
            "o": msg.get("o"),
            "h": msg.get("h"),
            "l": msg.get("l"),
            "c": msg.get("c"),
            "s": _normalize_ts(msg.get("s")),
            "e": _normalize_ts(msg.get("e")),
        }
    if ev == "V" and str(msg.get("T", "")).startswith("I:"):
        sym = str(msg["T"]).removeprefix("I:")
        return {
            "kind": "index_value",
            "symbol": sym,
            "c": msg.get("val"),
            "t": _normalize_ts(msg.get("t")),
        }
    if ev == "Q" and str(msg.get("sym", "")).startswith("O:"):
        bp = msg.get("bp")
        ap = msg.get("ap")
        mid = ((bp or 0) + (ap or 0)) / 2 if bp is not None and ap is not None else None
        spread_pct = None
        if mid and bp is not None and ap is not None and mid != 0:
            spread_pct = round(((ap - bp) / mid) * 100.0, 4)
        return {
            "kind": "opt_quote",
            "contract": msg.get("sym"),
            "t": _normalize_ts(msg.get("t") or msg.get("bt") or msg.get("at")),
            "bp": bp,
            "ap": ap,
            "mid": mid,
            "spread_pct": spread_pct,
            "nbbo": _nbbo_state(bp, ap),
        }
    return None
