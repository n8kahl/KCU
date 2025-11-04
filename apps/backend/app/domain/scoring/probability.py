from __future__ import annotations

from typing import Dict

from sklearn.isotonic import IsotonicRegression

from app.domain.types import ProbabilityBand

DEFAULT_WEIGHTS = {
    "TrendStack": 25,
    "Levels": 20,
    "Patience": 20,
    "ORB": 15,
    "Market": 10,
    "Options": 10,
}


def _calibrate(value: float) -> float:
    grid = [0, 0.3, 0.5, 0.7, 1]
    targets = [0.05, 0.25, 0.5, 0.75, 0.95]
    reg = IsotonicRegression(y_min=0.05, y_max=0.99, increasing=True)
    reg.fit(grid, targets)
    return float(reg.predict([value])[0])


def aggregate_probability(contributions: Dict[str, float], penalties: Dict[str, float], bonuses: Dict[str, float]) -> tuple[float, ProbabilityBand]:
    total_weight = sum(DEFAULT_WEIGHTS.values())
    weighted = 0.0
    for bucket, score in contributions.items():
        weight = DEFAULT_WEIGHTS.get(bucket, 5)
        weighted += score * weight
    base_score = (weighted / total_weight)
    calibrated = _calibrate(base_score)
    adj = (calibrated * 100) + sum(bonuses.values()) + sum(penalties.values())
    adj = max(min(adj, 99), 0)
    band = ProbabilityBand.from_score(adj)
    probability = round(adj / 100, 2)
    return probability, band
