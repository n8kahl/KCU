from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Set

from app.adapters.massive_ws import run_massive_ws
from app.core.settings import settings
from app.domain.features.microstructure import divergence_z, micro_chop, minute_thrust
from app.services.rings import (
    last_index_1m,
    last_index_1s,
    last_opt_quotes,
    push_index_1m,
    push_index_value,
    push_opt_quote,
)
from app.services.state_store import state_store
from app.services.tile_engine import merge_realtime_into_tile
from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)

_subscription_queue: asyncio.Queue[str] = asyncio.Queue()
_known_subscriptions: set[str] = set()
_subscription_lock = asyncio.Lock()
_last_broadcast: Dict[str, float] = {}
_contract_symbol_map: Dict[str, Set[str]] = {}

ETF_INDEX = {"SPY": "SPX", "QQQ": "NDX"}
BROADCAST_INTERVAL = 0.2  # seconds (≈5 Hz)


async def _ensure_subscription(params: str) -> None:
    if not params:
        return
    async with _subscription_lock:
        if params in _known_subscriptions:
            return
        _known_subscriptions.add(params)
    await _subscription_queue.put(params)


def _current_subscriptions() -> list[str]:
    return list(_known_subscriptions)


async def _bootstrap_index_subscriptions() -> None:
    seen = set()
    for symbol in settings.watchlist:
        idx = ETF_INDEX.get(symbol)
        if not idx or idx in seen:
            continue
        seen.add(idx)
        await _ensure_subscription(f"AM.I:{idx}")
        await _ensure_subscription(f"V.I:{idx}")
        # attempt per-second stream; ignore errors upstream if unavailable
        await _ensure_subscription(f"AS.I:{idx}")


async def _sync_option_contracts() -> None:
    while True:
        states = await state_store.all_states()
        contracts: set[str] = set()
        mapping: Dict[str, Set[str]] = {}
        for tile in states:
            opts = tile.options or {}
            bundle = opts.get("contracts") or {}
            primary = bundle.get("primary")
            backups: List[str] = bundle.get("backups") or []
            for contract in [primary, *backups]:
                if contract and contract.startswith("O:"):
                    contracts.add(contract)
                    mapping.setdefault(contract, set()).add(tile.symbol)
        for contract in contracts:
            await _ensure_subscription(f"Q.{contract}")
        global _contract_symbol_map
        _contract_symbol_map = mapping
        await asyncio.sleep(30)


async def _broadcast(symbol: str, tile_data: dict, manager: ConnectionManager) -> None:
    now = time.monotonic()
    last = _last_broadcast.get(symbol, 0.0)
    if now - last < BROADCAST_INTERVAL:
        return
    _last_broadcast[symbol] = now
    await manager.broadcast({"type": "tile", "data": tile_data})


async def _handle_index_event(symbol: str, manager: ConnectionManager) -> None:
    idx_bars = [bar for _, bar in last_index_1m(symbol, 40)]
    idx_closes = [bar.get("c") for bar in idx_bars if bar.get("c") is not None]
    if len(idx_closes) < 6:
        return
    thrust = minute_thrust(idx_closes, 5)
    prices_1s = [price for _, price in last_index_1s(symbol, 120)]
    returns = [(b - a) / a for a, b in zip(prices_1s, prices_1s[1:]) if a] if len(prices_1s) > 2 else []
    chop = micro_chop(returns)
    sec_variance = 0.0
    if returns:
        mean_val = sum(returns) / len(returns)
        sec_variance = sum((val - mean_val) ** 2 for val in returns) / len(returns)

    for etf, idx in ETF_INDEX.items():
        if idx != symbol:
            continue
        etf_state = await state_store.get_state(etf)
        etf_series = (etf_state.admin or {}).get("last_1m_closes") if etf_state else []
        divz = divergence_z(etf_series or idx_closes, idx_closes)
        tile = await merge_realtime_into_tile(
            etf,
            {
                "marketMicro": {
                    "minuteThrust": round(thrust, 4),
                    "microChop": round(chop, 4),
                    "divergenceZ": divz,
                    "secVariance": round(sec_variance, 6),
                }
            },
        )
        await _broadcast(etf, tile.model_dump(), manager)


def _quote_stats(contract: str) -> dict[str, Any] | None:
    now_ms = int(time.time() * 1000)
    window = [entry for entry in last_opt_quotes(contract, 600) if now_ms - entry[0] <= 60000]
    if not window:
        return None
    last_ts, last_doc = window[-1]
    nbbo_changes = 0
    for (_, prev), (_, curr) in zip(window, window[1:]):
        if prev.get("nbbo") != curr.get("nbbo"):
            nbbo_changes += 1
    duration = max((window[-1][0] - window[0][0]) / 1000, 1)
    flicker = nbbo_changes / duration
    spread_list = [doc.get("spread_pct") for _, doc in window if doc.get("spread_pct") is not None]
    avg_spread = spread_list[-1] if not spread_list else sum(spread_list) / len(spread_list)
    return {
        "flicker_per_sec": round(flicker, 4),
        "spread_pct": last_doc.get("spread_pct") or avg_spread,
        "nbbo": last_doc.get("nbbo"),
    }


async def _on_event(event: dict, manager: ConnectionManager) -> None:
    kind = event.get("kind")
    if kind == "index_value":
        push_index_value(event["symbol"], event.get("t"), event.get("c"))
        await _handle_index_event(event["symbol"], manager)
    elif kind == "index_1m":
        push_index_1m(event["symbol"], event.get("e"), {"o": event.get("o"), "h": event.get("h"), "l": event.get("l"), "c": event.get("c")})
        await _handle_index_event(event["symbol"], manager)
    elif kind == "opt_quote":
        push_opt_quote(event["contract"], event.get("t"), event)
        await _handle_option_quote(event, manager)


async def start_realtime(manager: ConnectionManager) -> None:
    await _bootstrap_index_subscriptions()
    asyncio.create_task(_sync_option_contracts())
    await run_massive_ws(lambda event: _on_event(event, manager), _subscription_queue, _current_subscriptions)


async def _handle_option_quote(event: dict, manager: ConnectionManager) -> None:
    contract = event.get("contract")
    if not contract:
        return
    symbols = _contract_symbol_map.get(contract)
    if not symbols:
        return
    stats = _quote_stats(contract)
    if not stats:
        return
    stats.update({"nbbo": event.get("nbbo"), "spread_pct": event.get("spread_pct") or stats.get("spread_pct")})
    for symbol in symbols:
        tile = await merge_realtime_into_tile(symbol, {"options": stats})
        await _broadcast(symbol, tile.model_dump(), manager)
