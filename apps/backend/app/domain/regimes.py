from __future__ import annotations


def detect_regime(atr_percentile: float, orb_range_pct: float, vix_proxy: float, spread_percentile: float) -> str:
    score = atr_percentile * 0.4 + orb_range_pct * 0.3 + vix_proxy * 0.2 + spread_percentile * 0.1
    if score > 0.65:
        return "Fast"
    if score > 0.4:
        return "Normal"
    return "Calm"
