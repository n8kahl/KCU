from __future__ import annotations


def market_filters(breadth: float, vix_trend: float, spy_alignment: float) -> dict:
    breadth_score = max(min(breadth, 1), 0)
    vix_penalty = max(1 - vix_trend, 0)
    spy_score = max(min(spy_alignment, 1), 0)
    score = round((breadth_score * 0.5 + vix_penalty * 0.2 + spy_score * 0.3), 3)
    return {
        "score": score,
        "reasons": [
            f"breadth: {breadth_score:.2f}",
            f"vix_penalty: {vix_penalty:.2f}",
            f"spy_alignment: {spy_score:.2f}",
        ],
    }
