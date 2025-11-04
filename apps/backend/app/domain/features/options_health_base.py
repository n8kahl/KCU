from __future__ import annotations


def options_health_base(spread_pct: float, oi_depth: int, iv_rank: float, nbbo_quality: str) -> dict:
    spread_score = max(1 - spread_pct / 15, 0)
    oi_score = min(oi_depth / 20000, 1)
    iv_score = max(1 - abs(iv_rank - 50) / 50, 0)
    nbbo_score = 1 if nbbo_quality == "stable" else 0.4
    score = round((spread_score * 0.4 + oi_score * 0.3 + iv_score * 0.2 + nbbo_score * 0.1), 3)
    return {
        "score": score,
        "reasons": [
            f"spread: {spread_score:.2f}",
            f"oi: {oi_score:.2f}",
            f"ivr: {iv_score:.2f}",
            f"nbbo: {nbbo_score:.2f}",
        ],
    }
