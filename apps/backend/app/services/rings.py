from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List, Tuple

_index_1s: Dict[str, Deque[Tuple[int, float]]] = {}
_index_1m: Dict[str, Deque[Tuple[int, dict]]] = {}
_option_quotes: Dict[str, Deque[Tuple[int, dict]]] = {}


def push_index_value(symbol: str, ts_ms: int | None, price: float | None, cap: int = 300) -> None:
    if ts_ms is None or price is None:
        return
    ring = _index_1s.setdefault(symbol, deque(maxlen=cap))
    ring.append((ts_ms, price))


def push_index_1m(symbol: str, end_ms: int | None, bar: dict, cap: int = 600) -> None:
    if end_ms is None or not bar:
        return
    ring = _index_1m.setdefault(symbol, deque(maxlen=cap))
    ring.append((end_ms, bar))


def push_opt_quote(contract: str, ts_ms: int | None, payload: dict, cap: int = 600) -> None:
    if ts_ms is None or not payload:
        return
    ring = _option_quotes.setdefault(contract, deque(maxlen=cap))
    ring.append((ts_ms, payload))


def last_index_1s(symbol: str, n: int = 120) -> List[Tuple[int, float]]:
    data = list(_index_1s.get(symbol, ()))
    return data[-n:]


def last_index_1m(symbol: str, n: int = 60) -> List[Tuple[int, dict]]:
    data = list(_index_1m.get(symbol, ()))
    return data[-n:]


def last_opt_quotes(contract: str, n: int = 60) -> List[Tuple[int, dict]]:
    data = list(_option_quotes.get(contract, ()))
    return data[-n:]
