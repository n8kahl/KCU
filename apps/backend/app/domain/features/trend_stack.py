from __future__ import annotations

from statistics import mean
from typing import Iterable


def trend_stack(vwap_slope: float, ema_fast: float, ema_slow: float, structure_flags: Iterable[int]) -> dict:
    flags = list(structure_flags) or [0]
    structure = sum(flags) / len(flags)
    ema_alignment = 1 if ema_fast > ema_slow else 0.3
    slope = max(min(vwap_slope / 0.1, 1), 0)
    score = round(mean([structure, ema_alignment, slope]), 3)
    return {
        "score": score,
        "reasons": [
            f"structure: {structure:.2f}",
            f"ema_alignment: {ema_alignment:.2f}",
            f"vwap_slope: {slope:.2f}",
        ],
    }
