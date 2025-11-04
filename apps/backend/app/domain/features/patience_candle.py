from __future__ import annotations


def patience_candle_quality(body_pct_atr: float, wick_ratio: float, volume_z: float) -> dict:
    body_score = min(body_pct_atr / 0.6, 1)
    wick_score = max(1 - abs(wick_ratio - 1), 0)
    volume_score = max(min(volume_z / 2, 1), 0)
    score = round((body_score + wick_score + volume_score) / 3, 3)
    return {
        "score": score,
        "reasons": [
            f"body%: {body_score:.2f}",
            f"wick: {wick_score:.2f}",
            f"volume: {volume_score:.2f}",
        ],
    }
