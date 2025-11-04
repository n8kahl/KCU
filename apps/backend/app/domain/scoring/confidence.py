from __future__ import annotations

from math import sqrt


def confidence_interval(sample_success: int, sample_total: int, regime: str) -> dict[str, float]:
    total = max(sample_total, 1)
    alpha = 1 + sample_success
    beta = 1 + (total - sample_success)
    mean = alpha / (alpha + beta)
    variance = (alpha * beta) / (((alpha + beta) ** 2) * (alpha + beta + 1))
    sigma = sqrt(variance)
    widen = 1.2 if regime == "Fast" else 1.0
    return {
        "p50": round(mean, 3),
        "p68": round(min(mean + sigma * widen, 0.99), 3),
        "p95": round(min(mean + sigma * 2 * widen, 0.99), 3),
    }
