from __future__ import annotations

from math import sqrt
from statistics import mean
from typing import Iterable


def minute_thrust(closes: Iterable[float], lookback: int = 5) -> float:
    values = [c for c in closes if c]
    if len(values) < lookback + 1:
        return 0.0
    recent = values[-(lookback + 1) :]
    moves = [(b - a) / a for a, b in zip(recent[:-1], recent[1:]) if a]
    if not moves:
        return 0.0
    pos = sum(1 for r in moves if r > 0)
    neg = len(moves) - pos
    thrust = (pos - neg) / len(moves)
    return max(-1.0, min(1.0, thrust))


def micro_chop(returns_1s: Iterable[float]) -> float:
    data = list(returns_1s)
    if len(data) < 10:
        return 0.0
    flips = sum(1 for a, b in zip(data, data[1:]) if (a > 0) != (b > 0))
    flips_norm = min(1.0, flips / 30.0)
    mu = mean(data)
    variance = sum((x - mu) ** 2 for x in data) / max(1, len(data) - 1)
    sigma = sqrt(max(variance, 0.0))
    # lower variance = higher chop penalty, invert
    var_norm = 1.0 - min(1.0, sigma / 0.004)
    return max(0.0, min(1.0, 0.6 * flips_norm + 0.4 * var_norm))


def divergence_z(etf_closes: Iterable[float], idx_closes: Iterable[float], window: int = 20) -> float:
    etf = [c for c in etf_closes if c]
    idx = [c for c in idx_closes if c]
    length = min(len(etf), len(idx), window)
    if length < 5:
        return 0.0
    etf = etf[-length:]
    idx = idx[-length:]
    diffs = []
    for (a0, a1), (b0, b1) in zip(zip(etf[:-1], etf[1:]), zip(idx[:-1], idx[1:])):
        if not a0 or not b0:
            continue
        diffs.append((a1 - a0) / a0 - (b1 - b0) / b0)
    if len(diffs) < 3:
        return 0.0
    mu = mean(diffs)
    variance = sum((x - mu) ** 2 for x in diffs) / max(1, len(diffs) - 1)
    sigma = sqrt(max(variance, 1e-6))
    return round(mu / sigma, 4)
